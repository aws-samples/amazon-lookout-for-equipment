import boto3
import json
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import sys

from l4ecwcw import *
from io import StringIO
import matplotlib.ticker as mtick

# Mandatory to ensure text is rendered in SVG plots:
matplotlib.rcParams['svg.fonttype'] = 'none'
dpi = 100

# Making Lookout for Equipment client available to all methods in this Lambda:
l4e_client = boto3.client('lookoutequipment')
s3 = boto3.resource('s3')

def get_execution_summary(event, context):
    """
    Entry point of the lambda function
    
    Returns:
        widget_html (string): an HTML-formatted string that can be displayed
        by a CloudWatch custom widgets
    """
    scheduler_name = event['scheduler_name']
    widget_context = event['widgetContext']
    width          = widget_context['width']
    height         = widget_context['height']
    
    svg = build_execution_summary(scheduler_name, width, height)
    return svg

def build_execution_summary(scheduler_name, width, height):
    list_executions = execution_summaries = list_inference_executions(
        scheduler_name,
        start_time=None,
        end_time=None,
        execution_status=None
    )
    
    # Loops through the executions summaries:
    results_json = []
    for execution_summary in list_executions:
        # We only request an output if the inference execution is a sucess:
        status = execution_summary['Status']
        if status == 'SUCCESS':
            # Download the JSON-line file locally:
            bucket = execution_summary['CustomerResultObject']['Bucket']
            key = execution_summary['CustomerResultObject']['Key']
            current_timestamp = key.split('/')[-2]
            local_fname = os.path.join('/tmp', f'{scheduler_name}_{current_timestamp}.jsonl')

            if not os.path.exists(local_fname):
                content_object = s3.Object(bucket, key)
                file_content = content_object.get()['Body'].read().decode('utf-8')
                with open(local_fname, 'w') as f:
                    f.write(file_content)

            # Opens the file and concatenate the results into a dataframe:
            with open(local_fname, 'r') as f:
                content = [eval(line) for line in f.readlines()]
                results_json = results_json + content

    # Build the final dataframes with all the results:
    results_df = pd.DataFrame(results_json)
    results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
    results_df = results_df.set_index('timestamp')
    results_df = results_df.sort_index()
    
    expanded_results = expand_signal_diagnostics(results_df)
    expanded_results = expanded_results[expanded_results['prediction'] == 1]
    
    if expanded_results.shape[0] > 0:
        event_details = pd.DataFrame(expanded_results.iloc[-1, 1:]).reset_index()

        event_details.columns = ['name', 'value']
        event_details = event_details.sort_values(by='value', ascending=False)
        event_details = event_details.iloc[:15, :].reset_index(drop=True)
        event_details = event_details.sort_values(by='value', ascending=True)
        
        title = f'Last event detected at {expanded_results.index[-1]}'
        html = plot_single_diagnostic(
            event_details, 
            len(expanded_results.columns) - 1, 
            title,
            width, 
            height
        )
        
    else:
        html = '<div>No anomaly detected by this scheduler yet</div>'
    
    return html

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

def expand_signal_diagnostics(results_df):
    expanded_results = []
    for index, row in results_df.iterrows():
        new_row = dict()
        new_row.update({'timestamp': index})
        new_row.update({'prediction': row['prediction']})

        if row['prediction'] == 1:
            diagnostics = pd.DataFrame(row['diagnostics'])
            diagnostics = dict(zip(diagnostics['name'], diagnostics['value']))
            new_row = {**new_row, **diagnostics}

        expanded_results.append(new_row)

    expanded_results = pd.DataFrame(expanded_results)
    expanded_results['timestamp'] = pd.to_datetime(expanded_results['timestamp'])
    expanded_results = expanded_results.set_index('timestamp')
    
    return expanded_results

def plot_single_diagnostic(event_details, num_signals, title, width, height):
    # We can then plot a horizontal bar chart:
    colors = set_aws_stylesheet()
    y_pos = np.arange(event_details.shape[0])
    values = list(event_details['value'])
    threshold = 1 / num_signals
    signal_color = {v: assign_color(v, threshold, colors) for v in values}
    signal_color = list(signal_color.values())

    # fig = plt.figure(figsize=(12,10))
    fig = plt.figure(figsize=(width/dpi, height/dpi), dpi=dpi)
    ax = plt.subplot(1,1,1)
    ax.barh(y_pos, event_details['value'], align='center', color=signal_color)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(event_details['name'])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    # Add the values in each bar:
    for i, v in enumerate(values):
        if v == 0:
            ax.text(0.0005, i, f'{v*100:.2f}%', color='#000000', verticalalignment='center')
        else:
            ax.text(0.0005, i, f'{v*100:.2f}%', color='#FFFFFF', fontweight='bold', verticalalignment='center')

    ax.vlines(x=threshold, ymin=-0.5, ymax=np.max(y_pos) + 0.5, linestyle='--', linewidth=2.0, color=colors[0])
    ax.vlines(x=threshold, ymin=-0.5, ymax=np.max(y_pos) + 0.5, linewidth=4.0, alpha=0.3, color=colors[0])
    plt.title(title)

    svg_io = StringIO()
    fig.savefig(svg_io, format="svg", bbox_inches='tight')
    
    return svg_io.getvalue().replace('DejaVu Sans', 'Amazon Ember')