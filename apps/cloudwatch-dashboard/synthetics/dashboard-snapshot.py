import asyncio
import json
import os
import urllib.parse
import urllib.request
import time

from aws_synthetics.selenium import synthetics_webdriver as webdriver
from aws_synthetics.common import synthetics_logger as logger
from aws_synthetics.common import synthetics_configuration

def setup():
    """
    Builds the initial AWS console URL and get appropriate credentials 
    to authenticate
    
    Returns:
        url: string
            The signin URL with an authentication token 
            obtained from the current session credentials
    """
    region = os.environ['AWS_REGION']
    signin_token = get_signin_token()
    console_url = f'https://console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:';
    url = get_signin_url(signin_token, console_url);
    
    return url
    
def get_signin_token():
    """
    Gets a signin token from the current session credentials
    
    Returns:
        signin_token: string
            JSON-formatted string with the signin token ready to be used
            in a signin URL
    """
    temp_creds = {
        'sessionId': os.environ['AWS_ACCESS_KEY_ID'],
        'sessionKey': os.environ['AWS_SECRET_ACCESS_KEY'],
        'sessionToken': os.environ['AWS_SESSION_TOKEN']
    }
    
    temp_creds = json.dumps(temp_creds, separators=(',', ':'))
    encoded_temp_creds = urllib.parse.quote(temp_creds, safe='~()*!.\'')
    request_url = f'https://signin.aws.amazon.com/federation?Action=getSigninToken&SessionType=json&Session={encoded_temp_creds}'
    
    req = urllib.request.Request(url=request_url)
    with urllib.request.urlopen(req) as response:
        signin_token = json.loads(response.read())['SigninToken']
        
    return signin_token
    
def get_signin_url(signin_token, console_url):
    """
    Build and encode a signin URL with a provided signin token
    and the URL to navigate to once authenticated.
    
    Parameters:
        signin_token (string):
            The JSON-formatted string with the signin token as obtained
            with the get_signin_token() method
        console_url (string):
            The URL to navigate to once authenticated
            
    Returns:
        url: string
            The signin URL
    """
    encoded_url = urllib.parse.quote(console_url, safe='~()*!.\'')
    url = f'https://signin.aws.amazon.com/federation?Action=login&Issuer=Lambda&Destination={encoded_url}&SigninToken={signin_token}';
    
    return url
    
async def get_dashboard_snapshot(signin_url):
    # Without a user_agent, some console UI are not rendered properly:
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
    syn_webdriver = webdriver
    viewport_height = int(os.environ['VIEWPORT_HEIGHT'])
    
    # User agents *MUST* be set before instanciating the browser object:
    await syn_webdriver.add_user_agent(user_agent)
    browser = syn_webdriver.Chrome()
    browser.set_viewport_size(1920, viewport_height)
    
    # Set CloudWatch synthetics configuration:
    synthetics_configuration.set_config({
       "screenshot_on_step_start" : False,
       "screenshot_on_step_success": True,
       "screenshot_on_step_failure": False
    });
    
    # Defines the different actions we want to execute in this canary:
    def navigate_to_dashboards_home():
        logger.info("### Navigate to the AWS CloudWatch dashboards list")
        browser.get(signin_url)
        time.sleep(5)
        
    def clean_interface():
        logger.info("### Remove clutter from the user interface")
        
        try:
            # Accept all cookies:
            browser.find_element_by_xpath('//span[text()="Accept all"]').click()
        except:
            logger.info("!!! Accept all cookies button not found")
        
        # Polaris UI opt-in:
        try:
            browser.find_element_by_class_name("console-polaris-opt-in-link").click()
        except:
            logger.info("!!! Polaris opt-in button not found")
        
        # Remove the blue ribbons with notifications appearing to the top:
        try:
            flash_elements_list = browser.find_element_by_class_name("awsui-flash-dismiss")
            
            # If there are several notifications, we want to remove them all:
            if isinstance(flash_elements_list, list):
                for element in flash_elements_list:
                    element.click()
            else:
                flash_elements_list.click()
        except:
            logger.info("!!! Notification ribbon not found")

    def navigate_to_dashboard():
        logger.info("### Navigate to the specific CloudWatch dashboard we are interested into")
        region = os.environ['AWS_REGION']
        dashboard = os.environ['DASHBOARD']
        dashboard_url = f'https://console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name={dashboard}';
        browser.get(dashboard_url)
        
        # We need to wait for some of the controls to appear on the UI
        # otherwise, the adjust_dashboard_ui() step will fail as it will
        # not find the HTML elements it needs:
        time.sleep(10)
        
    def adjust_dashboard_ui():
        logger.info("### Close the left menu-bar and switch to full screen")
        try:
            browser.find_element_by_class_name("awsui-app-layout__close-button").click()
        except Exception as e:
            logger.info("!!! Left menu bar close button not found")
            logger.info(e)
            
        try:
            # browser.find_element_by_class_name("awsui-flash-action-button").click()
            browser.find_element_by_xpath("//*[text()='Execute them all']").click()
        except Exception as e:
            logger.info("!!! Allow lambda executions button not found")
            logger.info(e)

        try:
            browser.find_element_by_class_name("fullscreen-button").click()
        except Exception as e:
            logger.info("!!! Full screen button not found")
            logger.info(e)

        #browser.find_element_by_xpath('//awsui-button[@data-test-id="refresh-dashboard-button"]').click()
        
        dashboard_type = os.environ['DASHBOARD_TYPE']
        if dashboard_type == 'ModelEvaluation':
            time.sleep(90)
        else:
            time.sleep(30)

    # Runs the action in sequence:
    await syn_webdriver.execute_step("navigateToDashboardsHome", navigate_to_dashboards_home)
    await syn_webdriver.execute_step("cleanUI", clean_interface)
    await syn_webdriver.execute_step("navigateToDashboard", navigate_to_dashboard)
    await syn_webdriver.execute_step("adjustDashboardUI", adjust_dashboard_ui)
    
    dashboard = os.environ['DASHBOARD']
    dashboard_type = os.environ['DASHBOARD_TYPE']
    stack_id = os.environ['STACK_ID']
    browser.save_screenshot('screenshot.png', f'{dashboard}-{dashboard_type}-{stack_id}')

    logger.info("Canary successfully executed")

# Canary entry point:
async def handler(event, context):
    signin_url = setup()

    return await get_dashboard_snapshot(signin_url)