# Imports
import boto3
import datetime
import json
import os
import time
import uuid

from l4ecwcw import *
from dashboards_definition import *

# Initialization
l4e_client     = boto3.client('lookoutequipment')
cw_client      = boto3.client('cloudwatch')
account_id     = boto3.client('sts').get_caller_identity()['Account']
session        = boto3.session.Session()
current_region = session.region_name
all_dashboards = None

# Entry point
def create_model_dashboard(event, context):
    """
    Entry point of the list models custom widgets. This function build
    an HTML table with all the Amazon Lookout for Equipment models found in 
    this account. The user can also create a dedicated dashboard for each
    model.
    
    Returns:
        html (string): an HTML formatted string with the table to be displayed
    """
    # If a model action is requested, we perform it
    # before displaying the dashboard:
    if 'dashboard_name' in event:
        process_dashboard_actions(event)
    
    # Get all the existing dashboard once and for all:
    global all_dashboards
    all_dashboards = build_dashboard_list()

    # Get time extent to show model from:    
    widget_context = event['widgetContext']
    start = widget_context['timeRange']['start']
    end = widget_context['timeRange']['end']
    start = datetime.datetime.fromtimestamp(start/1000, datetime.timezone.utc)
    end = datetime.datetime.fromtimestamp(end/1000, datetime.timezone.utc)

    # Get all the models in this account and display then in an HTML table:
    list_models = l4e_client.list_models()['ModelSummaries']
    
    # We only keep models created in the timeframe selected by the user:
    filtered_list_models = []
    for m in list_models:
        created = m['CreatedAt']
        if (created >= start) and (created <= end):
            filtered_list_models.append(m)

    html = generate_html_table(filtered_list_models)
    
    return html
    
def process_dashboard_actions(event):
    """
    Creates a dedicated dashboard for either a model,
    an asset or a fleet of assets
    """
    dashboard_name = event['dashboard_name']
    dashboard_type = event['dashboard_type']
    entity_name = event['entity_name']
    
    # Get the right dashboard definition 
    # depending on the asset we want to focus on:
    dashboard_body = eval(
        f'get_{dashboard_type}_dashboard_body("{entity_name}")'
    )
    
    # Create the new CloudWatch dashboard:
    cw_client.put_dashboard(
        DashboardName=dashboard_name,
        DashboardBody=json.dumps(dashboard_body)
    )
    
    create_synthetics(dashboard_name)
    
def create_synthetics(dashboard_name):
    client = boto3.client('synthetics')
    
    canary_name = 'modeleval-' + str(uuid.uuid4()).replace('-', '')[:11]
    version = os.getenv('VERSION')
    syn_source_bucket = os.getenv('SYN_SOURCE_BUCKET')
    syn_source_prefix = 'cloudwatch-dashboard-source-code'
    syn_source_code = f'{syn_source_prefix}/{version}/synthetics/canary-dashboard.zip'
    syn_execution_role = os.getenv('SYN_EXECUTION_ROLE')
    artifacts_s3_path = os.getenv('SYN_ARTIFACT_S3_PATH') + dashboard_name + '/'
    stack_id = os.getenv('Stack')

    response = client.create_canary(
        Name=canary_name,
        Code={
            'S3Bucket': syn_source_bucket,
            'S3Key': syn_source_code,
            'Handler': 'dashboard-snapshot.handler'
        },
        ArtifactS3Location=artifacts_s3_path,
        ExecutionRoleArn=syn_execution_role,
        Schedule={ 
            'Expression': 'rate(0 minute)',
            'DurationInSeconds': 0
        },
        RunConfig={
            'TimeoutInSeconds': 180,
            'MemoryInMB': 1024,
            'ActiveTracing': False,
            'EnvironmentVariables': {
                'DASHBOARD': dashboard_name,
                'STACK_ID': stack_id,
                'VIEWPORT_HEIGHT': '1850',
                'DASHBOARD_TYPE': 'ModelEvaluation'
            }
        },
        SuccessRetentionPeriodInDays=31,
        FailureRetentionPeriodInDays=31,
        RuntimeVersion='syn-python-selenium-1.0'
    )
    
    status = 'CREATING'
    while status != 'READY':
        response = client.get_canary(Name=canary_name)
        status = response['Canary']['Status']['State']
        time.sleep(1)
        
    response = client.start_canary(Name=canary_name)

def generate_html_table(list_models):
    header = (
        '<br /><div>Last <b>50 models</b> trained in the selected period (3 months by default):</div>'
        '<table>\n'
            '<thead>'
                '<tr>'
                    '<th>Dataset</th>'
                    '<th>Model</th>'
                    '<th>Training status</th>'
                    '<th>Model dashboard</th>'
                '</tr>'
            '</thead>\n'
    )
    
    footer = '</table>'
    
    body = '<tbody>\n'
    last_dataset = ''
    last_asset = ''
    
    # Loops through the model list to build the parameters we want to display:
    for model in list_models:
        model_params = dict()
        current_model = model['ModelName']
        current_dataset = model['DatasetName']
        
        # When we hit a new dataset we print its name:
        if current_dataset != last_dataset:
            model_params.update({'dataset': current_dataset})
            last_asset = ''

        # Otherwise we discard it:
        else:
            model_params.update({'dataset': '-'})
            model_params.update({'fleet_actions': ''})

        model_params.update({'model': current_model})
        
        current_status, model_actions = build_status_action(
            status=model['Status'],
            model_name=current_model
        )
        model_params.update({'status': current_status})
        model_params.update({'model_actions': model_actions})
        
        # We can now use the model_params we have
        # assembled to build an HTML row for this model:
        body += generate_html_row(model_params)
        last_dataset = current_dataset

        
    body += '</tbody>\n'
    
    html = header + body + footer
    
    return html
    
def build_entity_actions_buttons(dashboard_name, current_entity, entity_type):
    function = os.environ['AWS_LAMBDA_FUNCTION_NAME']
    global all_dashboards

    actions = create_button(
        action=f'arn:aws:lambda:{current_region}:{account_id}:function:{function}',
        payload={
            "dashboard_name": dashboard_name,
            "entity_name": current_entity,
            "dashboard_type": entity_type
        },
        label='Create',
        display_mode='widget',
        disabled=dashboard_name in all_dashboards
    )

    actions += create_link(
        href=f'#dashboards:name={dashboard_name}',
        label='View',
        disabled=not (dashboard_name in all_dashboards)
    )
    
    return actions
    
def build_status_action(status, model_name):
    # When a successfully trained model is found, we display the dashboard
    # management buttons:
    if status == 'SUCCESS':
        status = '<span style="font-weight: bold; color: #218306">SUCCESS</span>'
        
        model_actions = build_entity_actions_buttons(
            'L4E-Model-Dashboard-' + model_name, 
            model_name, 
            "model"
        )

    # Otherwise, we just display a "No model 
    # found" label next to the failed status
    else:
        status = f'<span style="font-weight: bold; color: #D13212">{status}</span>'
        model_actions = create_link(href='', label='No model found', disabled=True)
        
    return status, model_actions
    
def generate_html_row(model_params):
    # Build and output the row for the current model:
    row = '<tr>\n'
    row += f'<th>{model_params["dataset"]}</th>\n'
    row += f'<td>{model_params["model"]}</td>'
    row += f'<td style="text-align: center">{model_params["status"]}</td>'
    row += f'<td>{model_params["model_actions"]}</td>'
    row += '</tr>\n'

    return row