import boto3
import json
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from l4ecwcw import *
from io import StringIO
import matplotlib.ticker as mtick

# Mandatory to ensure text is rendered in SVG plots:
matplotlib.rcParams['svg.fonttype'] = 'none'
client = boto3.client('lookoutequipment')
dpi = 100

def plot_ranked_signals(event, context):
    model_name     = event['model_name']
    widget_context = event['widgetContext']
    width          = widget_context['width']
    height         = widget_context['height']
    
    svg = build_feature_importance(model_name, width, height)
    
    return svg

def build_feature_importance(model_name, width, height):    
    model_response = client.describe_model(ModelName=model_name)
    predictions = json.loads(model_response['ModelMetrics'])['predicted_ranges']
    start_date = pd.to_datetime(model_response['EvaluationDataStartTime']).tz_localize(None)
    end_date = pd.to_datetime(model_response['EvaluationDataEndTime']).tz_localize(None)

    df = pd.DataFrame(predictions)
    expanded_results = expand_results(df)
    num_values = len(list(expanded_results.columns))
    
    colors = set_aws_stylesheet()
    rank_df = pd.DataFrame(np.mean(expanded_results), columns=['value']).sort_values(by='value', ascending=True).tail(15)
    values = list(rank_df['value'])
    threshold = 1 / num_values
    signal_color = {v: assign_color(v, threshold, colors) for v in values}
    signal_color = list(signal_color.values())
    y_pos = np.arange(rank_df.shape[0])

    fig = plt.figure(figsize=(width/dpi, height/dpi), dpi=dpi)
    ax = plt.subplot(111)
    ax.barh(y_pos, rank_df['value'], align='center', color=signal_color)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(rank_df.index)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    # Add the values in each bar:
    for i, v in enumerate(values):
        if v > threshold:
            t = ax.text(0.001, i, f'{v*100:.2f}%', color='#000000', fontweight='bold', verticalalignment='center')
            t.set_bbox(dict(facecolor='#FFFFFF', alpha=0.5, pad=0.5, boxstyle='round4'))

    ax.vlines(x=1/num_values, ymin=-0.5, ymax=np.max(y_pos) + 0.5, linestyle='--', linewidth=2.0, color=colors[0])
    ax.vlines(x=1/num_values, ymin=-0.5, ymax=np.max(y_pos) + 0.5, linewidth=4.0, alpha=0.3, color=colors[0])
    ax.set_title('Aggregated signal importance over the evaluation period')
    
    svg_io = StringIO()
    fig.savefig(svg_io, format="svg", bbox_inches='tight')
    
    return svg_io.getvalue().replace('DejaVu Sans', 'Amazon Ember')