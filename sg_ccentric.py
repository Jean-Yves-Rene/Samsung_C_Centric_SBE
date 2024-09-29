import requests
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import hmac
import hashlib
import logging
from requests.exceptions import RequestException, ConnectTimeout

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Function to calculate HMAC-SHA256
def hmac_sha256(key, data):
    return hmac.new(key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()

def check_code_c_centric(imei):
    """Check the Samsung C Centrix code for the provided IMEI."""
    # Validate IMEI format
    if not imei.isdigit() or len(imei) not in [15, 16]:
        logging.error(f"Invalid IMEI format: {imei}. Must be 15 or 16 digits.")
        return "Invalid IMEI format. Please provide a valid IMEI."

    # Define the body as a JSON string
    body_string = f'{{"imei":"{imei}"}}'
    
    # Replace with your actual username and secret from environment variables
    username = os.getenv('USERNAME1')
    secret = os.getenv('SECRET')

    # Check if username and secret are available
    if not username or not secret:
        logging.error("Username or secret missing from environment variables.")
        return "Configuration error. Username or secret is not set."

    # Get the current date and time in ISO 8601 format
    x_datetime = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

    # Construct the signing key
    signing_key = secret + x_datetime

    # Construct the string to sign
    string_to_sign = f'{x_datetime}\n{body_string}'

    # Calculate the HMAC-SHA256 signature
    signature = hmac_sha256(signing_key, string_to_sign)

    # Construct the authorization header
    authorization = f'User:{username},Signature:{signature}'

    # Set headers for the request
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'x-datetime': x_datetime,
        'Authorization': authorization,
    }
    
    # Make an HTTP request
    url = 'https://greetme-api.cccsys.co.uk/ccbooking/api/v2/samsung-ref'

    # Proxy settings
    proxies = {
        'http': os.getenv('HTTP_PROXY'),
        'https': os.getenv('HTTPS_PROXY')
    }

    try:
        response = requests.post(url, json=json.loads(body_string), headers=headers, proxies=proxies, timeout=10)
        
        # Check the response status
        if response.status_code == 200:
            # Successful response
            data = response.json()
            ref_num = data.get('data', {}).get('refnum')  # Adjust the key here
            if ref_num and ref_num.endswith('-SKIP'):
                trimmed_ref_num = ref_num[:-5]  # Remove the '-SKIP' suffix
                logging.info("Success! The trimmed code is: %s", trimmed_ref_num)
                #return f"Success! The trimmed code is: {trimmed_ref_num}"
                return trimmed_ref_num
            else:
                logging.info("Success! The code is: %s", ref_num)
                #return f"Success! The code is: {ref_num}"
                return ref_num
        elif response.status_code == 404:
            logging.warning("There is no code for the provided IMEI.")
            return "Not found."
        else:
            logging.error("Error occurred: %s %s", response.status_code, response.text)
            return f"Error: {response.status_code}, {response.text}"

    except ConnectTimeout:
        logging.error("Request timeout error. The server did not respond in time.")
        return "Request timed out. Please try again later."
    except RequestException as e:
        logging.error("Request failed: %s", e)
        return f"Request failed: {e}"




# if __name__ == "__main__":
#     logging.info("*** Check Code Samsung C Centrix ***")
    
#     imei = input("\nPlease enter an IMEI (15 or 16 digits):\n")
#     result = check_code_c_centric(imei)  # Call the function
#     print(result)

    # Optionally test with a hardcoded IMEI
    #imei = "353079701096593"
    #result = check_code_c_centric(imei)  # Again, default retries will be used here
    #print(result)
