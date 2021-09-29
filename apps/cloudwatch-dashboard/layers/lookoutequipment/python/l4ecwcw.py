import boto3
import json
import matplotlib.pyplot as plt
import pandas as pd

l4e_client = boto3.client('lookoutequipment')
cw_client = boto3.client('cloudwatch')

def create_button(action, 
                  payload, 
                  label, 
                  display_mode='popup', 
                  disabled=False):
    """
    This function creates an HTML button the user can interact with from
    a CloudWatch custom widget.
    
    Parameters:
        action (string):
            The ARN of a lambda function to call when clicking on this button
        payload (string):
            A JSON formatted string that will be passed as argument to the
            lambda function used as endpoint for this button
        label (string):
            The label to use on the button
        display_mode (string):
            Can either be `popup` (display the result in a popup) or `widget` 
            (to replace the content of the current widget by the output of the 
            Lambda function used as endpoint). Defaults to `popup`
        disabled (boolean):
            Set to True to display a disabled button
            
    Returns:
        string: an HTML string with the button to display
    """
    if disabled:
        button_style = 'awsui-button-disabled'
        disabled = 'disabled=""'
        
    else:
        button_style = 'awsui-button awsui-button-variant-primary'
        disabled = ""
    
    button = (
        f'<a class="btn {button_style}" {disabled}>{label}</a>\n'
        '<cwdb-action '
            f'action="call" '
            f'endpoint="{action}" '
            f'display="{display_mode}">'
            f'{json.dumps(payload)}'
        '</cwdb-action>\n'
    )
    
    return button
    
def create_link(href, label, disabled=False):
    """
    Creates a simple button to redirect the user to a given link
    
    Parameters:
        href (string):
            The link to redirect the user to
        label (string):
            The label to use as the button label
        disabled (boolean):
            Set to True to display a disabled button. Defaults to False
            
    Returns:
        string: an HTML string with the button to display
    """
    if disabled:
        button_style = 'btn awsui-button-disabled'
        disabled = 'disabled=""'
        
    else:
        button_style = 'btn'
        disabled = ""
        
    if href != '':
        href = f'href="{href}"'
        
    button = f'<a class="{button_style}" {href} {disabled}>{label}</a>'
    
    return button
    
def get_dashboard_list(dashboard_name_prefix=None):
    """
    This function lists all the dashboards currently available in CloudWatch
    
    Parameters:
        dashboard_name_prefix (string):
            Filters out the dashboards that do not start with this prefix.
            Defaults to None (no filter)
            
    Returns:
        list of of CloudWatch dashboards found
    """
    cw_client = boto3.client('cloudwatch')
    if dashboard_name_prefix is None:
        response = cw_client.list_dashboards()
    else:
        response = cw_client.list_dashboards(
            DashboardNamePrefix=dashboard_name_prefix
        )
        
    dashboard_entries = []
    for dashboard in response['DashboardEntries']:
        dashboard_entries.append(dashboard['DashboardName'])
        
    return dashboard_entries
    
def dashboard_exists(dashboard_name):
    """
    Checks if a dashboard with this name exists
    
    Parameters:
        dashboard_name (string):
            Name of the dashboard to check existence for
    
    Returns:
        Boolean: returns True if a dashboard with this name already exists and 
        False otherwise.
    """
    # Lists all the dashbard with a name that starts with the searched string:
    list_dashboard = get_dashboard_list(dashboard_name)
    
    return dashboard_name in list_dashboard
    
def build_dashboard_list(client=None):
    """
    Query CloudWatch to list all existing dashboard in the current account
    
    Parameters:
        client (boto3.Client):
            A boto3 client to query the CloudWatch service. Defaults to None
            
    Returns:
        dashboard_entries (list): a list with the name of all the dashboards 
        found in this account
    """
    if client is None:
        response = cw_client.list_dashboards()
    else:
        response = client.list_dashboards()
        
    dashboard_entries = []
    for dashboard in response['DashboardEntries']:
        dashboard_entries.append(dashboard['DashboardName'])
        
    return dashboard_entries
    
def get_model_tags(model_name):
    """
    List of the tags in a key/value dictionary associated to a given Lookout
    for Equipment model.
    
    Parameters:
        model_name (string):
            Name of the model we want the tags list from
            
    Returns:
        tags (Dict): a dictionnary with all the tags keys and values that are
        attached to the model passed as argument
    """
    model_arn = l4e_client.describe_model(ModelName=model_name)['ModelArn']
    model_tags = l4e_client.list_tags_for_resource(ResourceArn=model_arn)['Tags']
    
    tags = dict()
    for tag in model_tags:
        tags.update({tag['Key']: tag['Value']})
    
    return tags
    
def set_aws_stylesheet():
    """
    This function loads a color branding consistent with the Polaris design
    the CloudWatch console if using
    
    Returns:
        colors (List): a list of all colors defined in this template
    """
    # Load AWS light background style sheet:
    plt.style.use('/opt/python/aws_color_branding_light.mpl')

    # Get colors from custom AWS palette:
    prop_cycle = plt.rcParams['axes.prop_cycle']
    colors = prop_cycle.by_key()['color']
    
    return colors

def assign_color(value, threshold, colors):
    """
    Given a threshold, match the passed value with a color from the AWS color
    styles. Anything greater that the threshold will yield a red color, anything
    else with a green color
    
    Parameters:
        value (float):
            The value to consider
        threshold (float):
            The threshold to compare the value with
        colors (list of strings):
            A list of strings with hexadecimal definitions of colors
            
    Returns:
        string: an hexadecimal string coding red if the value is greater than
        the threshold and green otherwise
    """
    if value > threshold:
        return colors[5]
    else:
        return colors[9]
        
def get_matching_s3_keys(bucket, prefix='', suffix=''):
    """
    Generate the keys in an S3 bucket.

    Parameters:
        bucket (string):
            Name of the S3 bucket
        prefix (string):
            Only fetch keys that start with this prefix (optional)
        suffix (string):
            Only fetch keys that end with this suffix (optional)
    """
    s3 = boto3.client('s3')
    kwargs = {'Bucket': bucket}

    # If the prefix is a single string (not a tuple of strings), we can
    # do the filtering directly in the S3 API.
    if isinstance(prefix, str):
        kwargs['Prefix'] = prefix

    while True:
        # The S3 API response is a large blob of metadata.
        # 'Contents' contains information about the listed objects.
        resp = s3.list_objects_v2(**kwargs)
        
        try:
            for obj in resp['Contents']:
                key = obj['Key']
                if key.startswith(prefix) and key.endswith(suffix):
                    yield key
                    
        except KeyError:
            print(f'No object found in s3://{bucket}/{prefix}/')

        # The S3 API is paginated, returning up to 1000 keys at a time.
        # Pass the continuation token into the next response, until we
        # reach the final page (when this field is missing).
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break
        
def convert_ranges(ranges_df, start_date, end_date, default_freq='1min'):
    """
    This method expands a list of ranges into an datetime index 
    pandas.Series

    Parameters:
        ranges_df (pandas.DataFrame):
            A dataframe with two columns, the start and end timestamp of
            each event
        default_freq (string):
            The default frequency to generate the time range for. This will
            be used to generate the DateTimeIndex for this pandas.Series

    Returns:
        pandas.DataFrame: a dataframe with a DateTimeIndex spanning from the
        minimum to the maximum timestamps present in the input dataframe.
        This will be a single Series named "Label" where a value of 1.0
        will correspond to the presence of an event (labels or anomalies).
    """
    range_index = pd.date_range(
        start=start_date,
        end=end_date, 
        freq=default_freq
    )
    range_data = pd.DataFrame(index=range_index)
    range_data.loc[:, 'Label'] = 0.0

    for _, row in ranges_df.iterrows():
        event_start = row[0]
        event_end = row[1]
        range_data.loc[event_start:event_end, 'Label'] = 1.0

    return range_data
    
def plot_ranges(range_df, range_title, color, ax):
    """
    Plot a range with either labelled or predicted events as a filled
    area positionned under the timeseries data.

    Parameters:
        range_df (pandas.DataFrame):
            A DataFrame that must contain at least a DateTimeIndex and a
            column called "Label"
        range_title (string):
            Title of the ax containing this range
        color (string):
            A string used as a color for the filled area of the plot
        ax (matplotlib.pyplot.Axis):
            The ax in which to render the range plot
    """
    ax.plot(range_df['Label'], color=color)
    ax.axes.get_xaxis().set_ticks([])
    ax.axes.get_yaxis().set_ticks([])
    ax.set_xlabel(range_title, fontsize=12)
    
def expand_results(df):
    """
    Let's first expand the results to expose the content of the diagnostics 
    column above into different dataframe columns
    """
    expanded_results = []
    for _, row in df.iterrows():
        new_row = dict()
        new_row.update({'start': row['start']})
        new_row.update({'end': row['end']})
        new_row.update({'prediction': 1.0})

        diagnostics = pd.DataFrame(row['diagnostics'])
        diagnostics = dict(zip(diagnostics['name'], diagnostics['value']))
        new_row = {**new_row, **diagnostics}

        expanded_results.append(new_row)

    expanded_results = pd.DataFrame(expanded_results)
    tags_list = expanded_results.columns[3:]
    tags_list = {t.split('\\')[-1]: t for t in tags_list}
    
    df_list = []
    for _, row in expanded_results.iterrows():
        new_index = pd.date_range(start=row['start'], end=row['end'], freq='1T')
        new_df = pd.DataFrame(index=new_index)

        for tag, col in tags_list.items():
            new_df[tag] = row[col]

        df_list.append(new_df)

    expanded_results_v2 = pd.concat(df_list, axis='index')
    
    return expanded_results_v2
    
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