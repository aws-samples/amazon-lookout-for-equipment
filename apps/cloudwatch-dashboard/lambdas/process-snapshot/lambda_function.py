import boto3
import json
import os
import urllib.parse

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

print('### New snapshot detected')

# Create a client available throughout the function:
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

def lambda_handler(event, context):
    print(json.dumps(event))
    
    # Get the object bucket and key from the event:
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], 
        encoding='utf-8'
    )

    dashboard_name = key.split('/')[-1]
    dashboard_type = dashboard_name.split('-')[-2]
    model_name = None
    scheduler_name = None
    if dashboard_type == 'Scheduler':
        scheduler_name = '-'.join(dashboard_name[38:].split('-')[:-2])
    elif dashboard_type == 'ModelEvaluation':
        model_name = '-'.join(dashboard_name[34:].split('-')[:-2])
        
    snapshot_fname = os.path.join('/tmp', dashboard_name)
    s3_client.download_file(bucket, key, snapshot_fname)
    with open(snapshot_fname, 'rb') as f:
        snapshot_content = f.read()
    
    email_snapshot(
        scheduler_name=scheduler_name,
        model_name=model_name,
        email=os.getenv('TargetEmail'),
        ses_region=os.getenv('SESRegion'),
        snapshot_content=snapshot_content
    )
    
    return {
        'statusCode': 200
    }
    
def email_snapshot(scheduler_name, model_name, email, ses_region, snapshot_content):
    if scheduler_name is None:
        subject = f"Latest dashboard snapshot for model: {model_name}"
        
    elif model_name is None:
        subject = f"Latest dashboard snapshot for scheduler: {scheduler_name}"
        
    html = f"<h3>{subject}</h3>\n"
    
    msg = MIMEMultipart()
    mimeImg = MIMEImage(snapshot_content)
    mimeImg.add_header('Content-ID', '<img-0>')
    html += "<center><img src='cid:img-0'></center>\n"
    msg.attach(mimeImg)

    msg['Subject'] = subject
    msg['From'] = email
    msg['To'] = email
    msg.attach(MIMEText(html, 'html'))
    ses = boto3.client('ses', region_name=ses_region)
    return ses.send_raw_email(
        Source=msg['From'], 
        Destinations=[email], 
        RawMessage={'Data': msg.as_string()}
    )