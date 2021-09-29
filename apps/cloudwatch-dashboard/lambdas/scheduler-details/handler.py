import boto3
import json
import sys

from datetime import datetime, timedelta

# Making Lookout for Equipment client available to all methods in this Lambda:
l4e_client = boto3.client('lookoutequipment')

def get_scheduler_details(event, context):
    """
    Entry point of the lambda function
    
    Returns:
        widget_html (string): an HTML-formatted string that can be displayed
        by a CloudWatch custom widgets
    """
    scheduler_name = event['scheduler_name']
    html = build_scheduler_details(scheduler_name)
    return html

def build_scheduler_details(scheduler_name):
    """
    Extract the scheduler attributes from the scheduler name passed as an argument
    
    Params:
        scheduler_name (string): name of the scheduler to get the attributes for
    """
    # Get attributes from the scheduler
    response      = l4e_client.describe_inference_scheduler(InferenceSchedulerName=scheduler_name)
    input_config  = response['DataInputConfiguration']
    output_config = response['DataOutputConfiguration']
    
    tz_offset        = input_config['InputTimeZoneOffset']
    input_bucket     = input_config['S3InputConfiguration']['Bucket']
    input_prefix     = input_config['S3InputConfiguration']['Prefix']
    input_s3_path    = f's3://{input_bucket}/{input_prefix}'
    timestamp_format = input_config['InferenceInputNameConfiguration']['TimestampFormat']
    delimiter        = input_config['InferenceInputNameConfiguration']['ComponentTimestampDelimiter']
    output_bucket    = output_config['S3OutputConfiguration']['Bucket']
    output_prefix    = output_config['S3OutputConfiguration']['Prefix']
    output_s3_path   = f's3://{output_bucket}/{output_prefix}'
    frequency        = response['DataUploadFrequency']
    
    date_format = '%Y-%m-%d %H:%M:%S'
    current_time, start_time, end_time, next_wakeup_time, next_timestamp = get_next_time_range(timestamp_format, frequency)
    
    next_execution = '<ul>'
    next_execution += '<li>Current time is <b>' + datetime.strftime(current_time, date_format) + '</b></li>'
    next_execution += '<li>Next execution time: <b>' + datetime.strftime(next_wakeup_time, date_format) + '</b></li>'
    next_execution += '<li>Next file: ' + f'<b><i>&lt;component&gt;</i>{delimiter}{next_timestamp}.csv</b>' + '</li>'
    next_execution += '<li>' + f'Timestamps must be between <b>{start_time}</b> and <b>{end_time}</b>' + '</li>'
    next_execution += '</ul>'
    
    num_executions, last_execution_time, last_success_time = get_last_execution(scheduler_name, date_format)
    last_execution = '<ul>'
    last_execution += f'<li>Executed <b>{num_executions}</b> times</li>'
    last_execution += f'<li>Last execution time: <b>{last_execution_time}</b></li>'
    
    if last_execution_time == last_success_time:
        last_execution += f'<li>Last successful execution: <b>{last_success_time}</b></li>'
    else:
        last_execution += f'<li>Last successful execution: <b><span style="color: #CC0000">{last_success_time}</span></b></li>'
    last_execution += '</ul>'
    
    # Build a dictionnary with all the model 
    # parameters we want to expose in the widget:
    scheduler_infos = dict()
    scheduler_infos.update({
        'Input': input_s3_path,
        'Output': output_s3_path,
        'File format': f'<i>&lt;component&gt;</i>{delimiter}{timestamp_format}.csv',
        'Next execution': next_execution,
        'Last execution': last_execution
    })

    # Generates the HTML of the widget:
    html = scheduler_info_widget(scheduler_infos)
        
    return html
    
def get_last_execution(scheduler_name, date_format):
    list_executions = execution_summaries = list_inference_executions(
        scheduler_name,
        start_time=None,
        end_time=None,
        execution_status=None
    )
    
    num_executions = len(list_executions)
    last_execution_time = datetime.strftime(list_executions[0]['ScheduledStartTime'], date_format)
    for inference_exec in list_executions:
        if inference_exec['Status'] == 'SUCCESS':
            last_success_time = datetime.strftime(inference_exec['ScheduledStartTime'], date_format)
            break
            
    
    
    return num_executions, last_execution_time, last_success_time
    
def list_inference_executions(scheduler_name,
                              execution_status=None, 
                              start_time=None, 
                              end_time=None, 
                              max_results=50):
    """
    This method lists all the past inference execution triggered by a
    given scheduler.
    
    PARAMS
    ======
        execution_status: string (default: None)
            Only keep the executions with a given status
            
        start_time: pandas.DateTime (default: None)
            Filters out the executions that happened before start_time
            
        end_time: pandas.DateTime (default: None)
            Filters out the executions that happened after end_time
            
        
        max_results: integer (default: 50)
            Max number of results you want to get out of this method
    
    RETURNS
    =======
        results_df: list of dict
            A list of all past inference executions, with each inference
            attributes stored in a python dictionary
    """
    # Built the execution request object:
    list_executions_request = {"MaxResults": max_results}
    list_executions_request["InferenceSchedulerName"] = scheduler_name
    if execution_status is not None:
        list_executions_request["Status"] = execution_status
    if start_time is not None:
        list_executions_request['DataStartTimeAfter'] = start_time
    if end_time is not None:
        list_executions_request['DataEndTimeBefore'] = end_time

    # Loops through all the inference executed by the current scheduler:
    has_more_records = True
    list_executions = []
    while has_more_records:
        list_executions_response = l4e_client.list_inference_executions(
            **list_executions_request
        )
        if "NextToken" in list_executions_response:
            list_executions_request["NextToken"] = list_executions_response["NextToken"]
        else:
            has_more_records = False

        list_executions = list_executions + \
                          list_executions_response["InferenceExecutionSummaries"]

    # Returns all the summaries in a list:
    return list_executions

def get_next_time_range(timestamp_format, frequency):
    """
    Get the current time and derives the next time the scheduler will wake
    up, what timestamp it will look for to find the right input file to 
    process and which time range to filter out when opening this file.
    """
    # Derive the appropriate time strftime format:
    if timestamp_format == 'EPOCH':
        strftime_format = '%s'
    elif timestamp_format == 'yyyy-MM-dd-HH-mm-ss':
        strftime_format = '%Y-%m-%d-%H-%M-%S'
    elif timestamp_format == 'yyyyMMddHHmmss':
        strftime_format = '%Y%m%d%H%M%S'

    frequency = int(frequency[2:][:-1])
    # current_timezone = pytz.timezone('UTC')
    # current_time = datetime.now(current_timezone)
    current_time = datetime.now()
    next_time = current_time - timedelta(
        minutes=current_time.minute % int(frequency),
        seconds=current_time.second,
        microseconds=current_time.microsecond
    )
    next_wakeup_time = next_time + timedelta(minutes=+frequency)
    next_timestamp = (next_time).strftime(format=strftime_format)

    start_time = next_time
    end_time = start_time + timedelta(minutes=+frequency, seconds=-1)
    
    return current_time, start_time, end_time, next_wakeup_time, next_timestamp

def scheduler_info_widget(scheduler_infos):
    """
    Generates the HTML output exposing the scheduler infos. This output can be
    consumed and exposed by CloudWatch Custom Widget.
    
    Params:
        scheduler_infos (dict): the parameters to display in the widget
    """
    header = '<table>\n'
    footer = '</table>\n'
    
    rows = '<tbody>'
    for key, value in scheduler_infos.items():
        rows += '<tr>'
        rows += f'<th>{key}</th>'
        rows += f'<td>{value}</td>'
        rows += '</tr>'
    rows += '</tbody>\n'
    
    return header + rows + footer