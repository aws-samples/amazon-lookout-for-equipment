import boto3
import json
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from l4ecwcw import *
from io import StringIO, BytesIO
from matplotlib import gridspec

# Mandatory to ensure text is rendered in SVG plots:
matplotlib.rcParams['svg.fonttype'] = 'none'
client = boto3.client('lookoutequipment')
dpi = 100

def plot_feature_importance(event, context):
    model_name     = event['model_name']
    widget_context = event['widgetContext']
    width          = widget_context['width']
    height         = widget_context['height']
    
    try:
        output_format  = widget_context['output_format']
    except Exception as e:
        output_format = 'svg'
    
    svg = build_feature_importance(model_name, width, height, output_format)
    
    return svg

def build_feature_importance(model_name, width, height, output_format):    
    model_response = client.describe_model(ModelName=model_name)
    predictions = json.loads(model_response['ModelMetrics'])['predicted_ranges']
    start_date = pd.to_datetime(model_response['EvaluationDataStartTime']).tz_localize(None)
    end_date = pd.to_datetime(model_response['EvaluationDataEndTime']).tz_localize(None)

    df = pd.DataFrame(predictions)
    expanded_results = expand_results(df)
    predictions_df = convert_ranges(df, start_date, end_date)
    
    new_index = pd.date_range(
        start=np.min(predictions_df.index),
        end=np.max(predictions_df.index),
        freq='1D'
    )
    expanded_results = expanded_results.resample('1D').mean()
    expanded_results = expanded_results.reindex(index=new_index)
    expanded_results = expanded_results.replace(to_replace=np.nan, value=0.0)
    
    colors = set_aws_stylesheet()
    fig = plt.figure(figsize=(width*1.25/dpi, height/dpi), dpi=dpi)
    gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[10, 1], hspace=0.5)
    ax1 = fig.add_subplot(gs[0])
    x = expanded_results.index
    
    bottom_values = np.zeros((len(expanded_results.index),))
    for tag in list(expanded_results.columns):
        y = expanded_results.loc[:, tag]
        plt.bar(x=x, height=y, bottom=bottom_values, alpha=0.8, width=1.0)
        bottom_values += y.values
        
    ax1.set_title('Feature importance evolution by signal - Daily average')

    ax2 = fig.add_subplot(gs[1])
    plot_ranges(predictions_df, 'Detected events', colors[5], ax2)
    ax2.set_xlim(ax1.get_xlim())
    
    if output_format == 'png':
        png_io = BytesIO()
        fig.savefig(png_io, format="png", bbox_inches='tight')
        return png_io.getvalue()
        
    elif output_format == 'svg':
        svg_io = StringIO()
        fig.savefig(svg_io, format="svg", bbox_inches='tight')
        return svg_io.getvalue().replace('DejaVu Sans', 'Amazon Ember')