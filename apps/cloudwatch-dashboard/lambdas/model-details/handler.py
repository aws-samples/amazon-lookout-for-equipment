import boto3
import json
import sys
import os

from datetime import datetime

# Making Lookout for Equipment client available to all methods in this Lambda:
l4e_client = boto3.client('lookoutequipment')

def display_model_details(event, context):
    """
    Entry point of the lambda function
    
    Returns:
        widget_html (string): an HTML-formatted string that can be displayed
        by a CloudWatch custom widgets
    """
    widgetContext = event['widgetContext']
    dashboardName = widgetContext['dashboardName']
    width         = widgetContext['width']
    height        = widgetContext['height']

    widget_html = get_model_details(event, context)
    
    return widget_html
    
def get_model_details(event, context):
    """
    Extract the model attributes from the model passed as an argument
    """
    # Get attributes from both the model and the associated dataset:
    model_name       = event['model_name']

    model_response   = l4e_client.describe_model(ModelName=model_name)
    dataset_response = l4e_client.describe_dataset(DatasetName=model_response['DatasetName'])
    date_format      = '%Y-%m-%d %H:%M:%S'
    
    try:
        # Build a dictionnary with all the model 
        # parameters we want to expose in the widget:
        model_infos = dict()
        input_configuration = dataset_response['IngestionInputConfiguration']['S3InputConfiguration']
        model_infos.update({
            'Dataset': model_response['DatasetName'],
            'Training start': datetime.strftime(
                model_response['TrainingDataStartTime'], date_format
            ),
            'Training end': datetime.strftime(
                model_response['TrainingDataEndTime'], date_format
            ),
            'Evaluation start': datetime.strftime(
                model_response['EvaluationDataStartTime'], date_format
            ),
            'Evaluation end': datetime.strftime(
                model_response['EvaluationDataEndTime'], date_format
            )
        })
        
        # Generates the HTML of the widget:
        html = model_info_widget(model_infos)
        
    # Some older model / dataset won't include all the fields we're looking
    # for: catching these error and information the user.
    except KeyError as e:
        error_msg = f'Model or dataset attribute not found: {e}'
        html = f'<span style="color: #CC0000">{error_msg}</span>'

    except:
        error_msg = "Unexpected error:", sys.exc_info()[0]
        html = f'<span style="color: #CC0000">{error_msg}</span>'
        
    return html

def model_info_widget(model_infos):
    """
    Generates the HTML output exposing the model infos. This output can be
    consumed and exposted by CloudWatch Custom Widget.
    
    Params:
        model_infos (dict): the parameters to display in the widget
    """
    header = '<table>\n'
    footer = '</table>\n'
    
    row_header = '<tr>'
    row_values = '<tr>'
    for key, value in model_infos.items():
        row_header += f'<th>{key}</th>'
        row_values += f'<td>{value}</td>'

    row_header += '</tr>'
    row_values += '</tr>'
    body = row_header + '\n' + row_values
        
    body = f'<tbody>{body}</tbody>\n'
    
    return header + body + footer