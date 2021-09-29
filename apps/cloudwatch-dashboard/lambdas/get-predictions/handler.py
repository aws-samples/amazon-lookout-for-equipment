import boto3
import json
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from l4ecwcw import *
from io import StringIO
from matplotlib import gridspec

# Mandatory to ensure text is rendered in SVG plots:
matplotlib.rcParams['svg.fonttype'] = 'none'
client = boto3.client('lookoutequipment')
dpi = 100

def get_predictions(event, context):
    model_name     = event['model_name']
    widget_context = event['widgetContext']
    width          = widget_context['width']
    
    # Height taking into account the height of the tag selection form:
    height         = int(widget_context['height']) - 50
    
    tags_list = get_tags_list(model_name)
    tag = get_selected_tag(widget_context)
    if tag is None:
        tag = tags_list[0]
        
    svg = get_model_evaluations_infos(model_name, width, height, tag)
    html = build_tag_selection_form(event, context, tags_list, tag)
    html = html + f'<div>{svg}</div>'
    
    return html
    
def get_tags_list(model_name):
    model_response = client.describe_model(ModelName=model_name)
    predictions = json.loads(model_response['ModelMetrics'])['predicted_ranges']
    diagnostics = predictions[0]['diagnostics']
    tags_list = [d['name'].split('\\')[-1] for d in diagnostics]
    
    return tags_list
    
def get_selected_tag(widget_context):
    print(widget_context['forms']['all'])

    if len(widget_context['forms']['all']) > 0:
        return widget_context['forms']['all']['tags']
        
    else:
        return None

def get_model_evaluations_infos(model_name, width, height, tag):
    model_response = client.describe_model(ModelName=model_name)
    predictions = json.loads(model_response['ModelMetrics'])['predicted_ranges']
    start_date = pd.to_datetime(model_response['EvaluationDataStartTime']).tz_localize(None)
    end_date = pd.to_datetime(model_response['EvaluationDataEndTime']).tz_localize(None)

    df = pd.DataFrame(predictions)
    predictions_df = convert_ranges(df, start_date, end_date)
    events_df = df.copy()
    events_df['duration'] = pd.to_datetime(events_df['end']) - pd.to_datetime(events_df['start'])
    events_df['duration'] = events_df['duration'].dt.total_seconds() / 3600    
    
    component_name = json.loads(model_response['Schema'])['Components'][0]['ComponentName']
    dataset_name = model_response['DatasetName']
    dataset_response = client.describe_dataset(DatasetName=dataset_name)
    bucket = dataset_response['IngestionInputConfiguration']['S3InputConfiguration']['Bucket']
    prefix = dataset_response['IngestionInputConfiguration']['S3InputConfiguration']['Prefix'] #+ component_name + '/'
    df_list = []
    s3 = boto3.client('s3')
    for file_key in get_matching_s3_keys(bucket=bucket, prefix=prefix, suffix=('.csv', '.CSV')):
        try:
            print(f'Looking for {tag} data in file {file_key}...')
            csvfile = s3.get_object(Bucket=bucket, Key=file_key)
            df = pd.read_csv(csvfile['Body'], usecols=['Timestamp', tag])
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df = df.set_index('Timestamp')
            df = df[start_date:end_date]
            df_list.append(df)
            
        except Exception as e:
            print(f'Tag {tag} not found in file {file_key}')
            
    timeseries_df = pd.concat(df_list, axis='index')
    
    # Prepare the figure:
    colors = set_aws_stylesheet()
    fig = plt.figure(figsize=(width*1.25/dpi, height/dpi), dpi=dpi)
    gs = gridspec.GridSpec(nrows=4, ncols=1, height_ratios=[8, 1.5, 5, 5], hspace=0.5)
    
    # First section: a line plot of the selected time series:
    ax1 = fig.add_subplot(gs[0])
    plt.plot(timeseries_df)
    ax1.set_title(f'Tag: {tag}')
    
    # Second section: the events detected by Lookout for Equipment:
    ax2 = fig.add_subplot(gs[1])
    plot_ranges(predictions_df, 'Detected events', colors[5], ax2)
    ax2.set_xlim(ax1.get_xlim())
    
    # Third section: the number of detected events per day:
    ax3 = fig.add_subplot(gs[2])
    ax3.plot(predictions_df.rolling(60*24).sum())
    ax3.set_xlim(ax1.get_xlim())
    ax3.axes.get_xaxis().set_ticks([])
    ax3.set_xlabel('Number of daily event detected', fontsize=12)

    # # Fourth section: their averate duration:
    ax4 = fig.add_subplot(gs[3])
    ax4.bar(pd.to_datetime(events_df['start']), events_df['duration'], color=colors[9], width=2.0, alpha=0.5)
    ax4.set_xlim(ax1.get_xlim())
    ax4.axes.get_xaxis().set_ticks([])
    ax4.set_xlabel('Average duration of detected events', fontsize=12)

    # Save this image to an SVG string:
    svg_io = StringIO()
    fig.savefig(svg_io, format="svg", bbox_inches='tight')

    return svg_io.getvalue().replace('DejaVu Sans', 'Amazon Ember')
    
def build_tag_selection_form(event, context, tags_list, selected_tag):
    endpoint = context.invoked_function_arn
    payload = json.dumps(event)
    
    options = []
    tags_list.sort()
    for t in tags_list:
        if t == selected_tag:
            options.append(f'<option selected value="{t}">{t}</option>')
        else:
            options.append(f'<option value="{t}">{t}</option>')
            
    options = '\n'.join(options)
    
    form = (
        '<form>'
            '<table style="border: none; box-shadow: 0px 0px #000000"><tr><td>'
                '<label for="tags">Choose a tag to visualize the detected events against:</label>&nbsp;'
            '</td><td>'
                '<select name="tags" id="tags">' + options + '</select>&nbsp;\n'
            '</td><td>'
                '<a class="btn btn-primary">Submit</a>\n'
                f'<cwdb-action action="call" endpoint="{endpoint}">'
                f'{payload}'
                '</cwdb-action>'
            '</td></tr></table>'
        '</form>'
    )
    
    return form