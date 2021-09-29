# Initialization
import boto3
import os

account_id = boto3.client('sts').get_caller_identity()['Account']
session = boto3.session.Session()
current_region = session.region_name

def get_model_dashboard_body(model_name):
    stack = os.environ['Stack']
    if stack != '':
        stack = '-' + stack
    
    dashboard_body = {
       "start": "-P3M",
       "periodOverride": "inherit",
       "widgets": [{
            "x": 0, "y": 0, "height": 3, "width": 24, "type": "custom",
            "properties": {
                "endpoint": f"arn:aws:lambda:{current_region}:{account_id}:function:l4e-dashboard-model-details{stack}",
                "updateOn": {"refresh": True, "resize": True, "timeRange": False},
                "params": {"model_name": model_name},
                "title": f"{model_name} | Model details"
            }
        },
        {
            "x": 0, "y": 5, "height": 11, "width": 24, "type": "custom",
            "properties": {
                "endpoint": f"arn:aws:lambda:{current_region}:{account_id}:function:l4e-dashboard-get-predictions{stack}",
                "updateOn": {"refresh": True, "resize": True, "timeRange": True},
                "params": {"model_name": model_name},
                "title": "Detected anomalies"
            }
        },
        {
            "x": 0, "y": 11, "height": 10, "width": 24, "type": "custom",
            "properties": {
                "endpoint": f"arn:aws:lambda:{current_region}:{account_id}:function:l4e-dashboard-plot-ranked-signals{stack}",
                "updateOn": {"refresh": True, "resize": True, "timeRange": False},
                "params": {"model_name": model_name},
                "title": "Aggregated signal importance"
            }
        },
        {
            "x": 0, "y": 20, "height": 9, "width": 18, "type": "custom",
            "properties": {
                "endpoint": f"arn:aws:lambda:{current_region}:{account_id}:function:l4e-dashboard-plot-feature-importance{stack}",
                "updateOn": {"refresh": True, "resize": True, "timeRange": True},
                "params": {"model_name": model_name},
                "title": "Signal importance"
            }
        },
        {
            "x": 18, "y": 20, "height": 9, "width": 6, "type": "custom",
            "properties": {
                "endpoint": f"arn:aws:lambda:{current_region}:{account_id}:function:l4e-dashboard-plot-feature-importance-legend{stack}",
                "updateOn": {"refresh": False, "resize": False, "timeRange": False},
                "params": {"model_name": model_name},
                "title": "Signal importance legend"
            }
        }]
    }
    
    return dashboard_body