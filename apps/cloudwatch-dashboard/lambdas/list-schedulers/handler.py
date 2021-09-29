import boto3
import json
import os
import time
import uuid

from datetime import datetime

from l4ecwcw import *

l4e_client = boto3.client('lookoutequipment')
cw_client = boto3.client('cloudwatch')

account_id = boto3.client('sts').get_caller_identity()['Account']
session = boto3.session.Session()
current_region = session.region_name
stack = os.environ['Stack']
if stack != '':
    stack = '-' + stack

def create_scheduler_dashboard(event, context):
    """
    Entry point of the list scheduler custom widgets. This function build
    an HTML table with all the Amazon Lookout for Equipment inference
    scheduler found in this account. The user has the ability to stop and start
    each of them. The user can also create a dedicated dashboard for each
    scheduler.
    
    Returns:
        html (string): an HTML formatted string with the table to be displayed
    """
    
    if 'dashboard_name' in event:
        process_dashboard_actions(event)
       
    # If a scheduler action is requested, we perform it
    # before displaying the dashboard:
    elif 'scheduler_name' in event:
        process_scheduler_actions(event)
    
    # Get all the schedulers in this account and display then in an HTML table:
    schedulers_list = l4e_client.list_inference_schedulers()['InferenceSchedulerSummaries']
    html = generate_html_table(schedulers_list)
    
    return html
    
def process_scheduler_actions(event):
    scheduler_name = event['scheduler_name']
    action = event['action']
    
    if action == 'start_scheduler':
        response = l4e_client.start_inference_scheduler(
            InferenceSchedulerName=scheduler_name
        )
        
    else:
        response = l4e_client.stop_inference_scheduler(
            InferenceSchedulerName=scheduler_name
        )
        
def process_dashboard_actions(event):
    """
    Creates a dedicated dashboard for a scheduler, create and start a new
    CloudWatch Synthetics Canary to send a dashboard screenshot every Monday
    morning.
    """
    dashboard_name = event['dashboard_name']
    scheduler_name = event['scheduler_name']
    action = event['action']
    
    if action == 'create_dashboard':
        dashboard_body = {
           "start": "-P3M",
           "periodOverride": "inherit",
           "widgets": [{
                "x": 12, "y": 0, "height": 8, "width": 12,
                "type": "custom",
                "properties": {
                    "endpoint": f"arn:aws:lambda:{current_region}:{account_id}:function:l4e-dashboard-scheduler-details{stack}",
                    "updateOn": {
                        "refresh": True,
                        "resize": True,
                        "timeRange": False
                    },
                    "params": {
                        "scheduler_name": scheduler_name
                    },
                    "title": f"{scheduler_name} | Inference scheduler details"
                }
            },
            {
                "x": 0, "y": 0, "height": 8, "width": 12,
                "type": "custom",
                "properties": {
                    "endpoint": f"arn:aws:lambda:{current_region}:{account_id}:function:l4e-dashboard-scheduler-last-execution-details{stack}",
                    "updateOn": {
                        "refresh": True,
                        "resize": True,
                        "timeRange": True
                    },
                    "params": {
                        "scheduler_name": scheduler_name
                    },
                    "title": f"{scheduler_name} | Last execution diagnostics"
                }
            }
            ]
        }

        cw_client.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        create_synthetics(dashboard_name)
        
def create_synthetics(dashboard_name):
    client = boto3.client('synthetics')
    

    canary_name = 'scheduler-' + str(uuid.uuid4()).replace('-', '')[:11]
    version = os.getenv('VERSION')
    syn_source_bucket = os.getenv('SYN_SOURCE_BUCKET')
    syn_source_prefix = 'cloudwatch-dashboard-source-code'
    syn_source_code = f'{syn_source_prefix}/{version}/synthetics/canary-dashboard.zip'
    syn_execution_role = os.getenv('SYN_EXECUTION_ROLE')
    artifacts_s3_path = os.getenv('SYN_ARTIFACT_S3_PATH') + dashboard_name + '/'
    stack_id = os.getenv('Stack')
    snapshot_runs = os.getenv('SNAPSHOT_RUNS')
    
    if snapshot_runs == 'Manual':
        # Runs this canary only once, when it's started:
        schedule_expression = 'rate(0 minute)'
        
    elif snapshot_runs == 'Daily':
        # Runs this canary every morning of the business week at 6am:
        # Cron expression configuration reminder:
        # Minutes Hours Day-of-Month Month Day-of-Week Year
        schedule_expression = 'cron(0 6 ? * MON-FRI *)'
        
    elif snapshot_runs == 'Weekly':
        # Runs this canary every Monday morning at 6am:
        schedule_expression = 'cron(0 6 ? * MON *)'
    
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
            'Expression': schedule_expression,
            'DurationInSeconds': 0
        },
        RunConfig={
            'TimeoutInSeconds': 180,
            'MemoryInMB': 1024,
            'ActiveTracing': False,
            'EnvironmentVariables': {
                'DASHBOARD': dashboard_name,
                'STACK_ID': stack_id,
                'VIEWPORT_HEIGHT': '700',
                'DASHBOARD_TYPE': 'Scheduler'
            }
        },
        SuccessRetentionPeriodInDays=31,
        FailureRetentionPeriodInDays=31,
        RuntimeVersion='syn-python-selenium-1.0'
    )

def generate_html_row(scheduler_param):
    # If the scheduler is stopped, we allow the user to start it:
    if scheduler_param['status'] == 'STOPPED':
        status_button = create_button(
            action=f'arn:aws:lambda:{current_region}:{account_id}:function:l4e-dashboard-list-schedulers{stack}',
            payload={
                'scheduler_name': scheduler_param['name'],
                'action': 'start_scheduler'
            },
            label='Start',
            display_mode='widget'
        )
        
    # Otherwise, the only action is to stop it:
    else:
        status_button = create_button(
            action=f'arn:aws:lambda:{current_region}:{account_id}:function:l4e-dashboard-list-schedulers{stack}',
            payload={
                'scheduler_name': scheduler_param['name'],
                'action': 'stop_scheduler'
            },
            label ='Stop',
            display_mode='widget'
        )
        
        
    # If a dashboard for this scheduler already exists, we print a link to navigate to it:
    scheduler_name = scheduler_param['name']
    current_dashboard_name = 'L4E-Scheduler-Dashboard-' + scheduler_name
    # if current_dashboard_name in get_dashboard_list():
    if dashboard_exists(current_dashboard_name):
        dashboard_button = create_link(
            href=f'#dashboards:name={current_dashboard_name}"',
            label='View'
        )
        
    # Otherwise, we create a button to let the user create it:
    else:
        dashboard_button = create_button(
            action=f'arn:aws:lambda:{current_region}:{account_id}:function:l4e-dashboard-list-schedulers{stack}',
            payload={
                'dashboard_name': current_dashboard_name,
                'scheduler_name': scheduler_param['name'],
                'action': 'create_dashboard'
            },
            label='Create dashboard',
            display_mode='widget'
        )

    # Build the output row
    row = '<tr>'
    # row += '<th>' + scheduler_param['dataset'] + '</th>'
    row += '<td>' + scheduler_param['model'] + '</td>'
    row += '<td>' + scheduler_name + '</td>'
    row += f'<td>{status_button}</td>'
    row += f'<td>{dashboard_button}</td>'
    row += '</tr>'
    
    return row

def generate_html_table(schedulers_list):
    header = (
        '<table>\n'
            '<thead>\n'
                '<tr>'
                    # '<th>Dataset</th>'
                    '<th>Model</th>'
                    '<th>Scheduler</th>'
                    '<th>Status</th>'
                    '<th>Scheduler dashboard</th>'
                '</tr>\n'
            '</thead>\n'
    )
    
    footer = '</table>'
    
    body = '<tbody>\n'

    for scheduler in schedulers_list:
        response = l4e_client.describe_inference_scheduler(
            InferenceSchedulerName=scheduler['InferenceSchedulerName']
        )
        input_config  = response['DataInputConfiguration']
        output_config = response['DataOutputConfiguration']
        
        scheduler_param = {
            'name': scheduler['InferenceSchedulerName'],
            'model': scheduler['ModelName'],
            'status': scheduler['Status'],
            # 'dataset': l4e_client.describe_model(ModelName=scheduler['ModelName'])['DatasetName']
        }
        
        body += generate_html_row(scheduler_param) + '\n'

    body += '</tbody>\n'
    
    html = header + body + footer
    
    return html