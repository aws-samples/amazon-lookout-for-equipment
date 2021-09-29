import boto3
import json
import matplotlib
import matplotlib.pyplot as plt

from l4ecwcw import *
from io import StringIO

# Mandatory to ensure text is rendered in SVG plots:
matplotlib.rcParams['svg.fonttype'] = 'none'
l4e_client = boto3.client('lookoutequipment')
dpi = 100

def plot_feature_importance_legend(event, context):
    model_name     = event['model_name']
    widget_context = event['widgetContext']
    width          = widget_context['width']
    height         = widget_context['height']
    
    svg = build_feature_importance_legend(model_name, width, height)

    return svg

def build_feature_importance_legend(model_name, width, height):
    model_response = l4e_client.describe_model(ModelName=model_name)
    predictions = json.loads(model_response['ModelMetrics'])['predicted_ranges']

    diagnostics = predictions[0]['diagnostics']
    tags_list = [d['name'].split('\\')[-1] for d in diagnostics]
    colors = set_aws_stylesheet()
    matplotlib.rcParams['figure.facecolor'] = 'FFFFFF'
    palette = {s: colors[index % len(colors)] for index, s in enumerate(tags_list)}

    # Create legend handles manually:
    handles = [matplotlib.patches.Patch(color=palette[x], label=x) for x in palette.keys()]
    
    # Create legend:
    fig = plt.figure(figsize=(width/dpi, height/dpi), dpi=dpi)
    plt.legend(handles=handles, loc='upper left')
    plt.gca().set_axis_off()

    # Build the SVG from this figure:
    svg_io = StringIO()
    fig.savefig(svg_io, format="svg", bbox_inches='tight')
    
    return svg_io.getvalue().replace('DejaVu Sans', 'Amazon Ember')