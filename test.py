#@title C-Centric Code SG
import json
import hashlib
import os
import hmac
from datetime import datetime
import requests

# Get IMEI from user input
imei = input("Enter IMEI: ")

# Define the body as a JSON string
body_string = f'{{"imei":"{imei}"}}'

# Replace with your actual username and secret
username = 'ee-s-repair'
secret = '3249eca7fd91ae16da8fa9e3bb98e2d7'

# Get the current date and time in ISO 8601 format
x_datetime = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

# Function to calculate HMAC-SHA256
def hmac_sha256(key, data):
    return hmac.new(key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()

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
data = json.loads(body_string)
# Make an HTTP request
url = 'https://greetme-api.cccsys.co.uk/ccbooking/api/v2/samsung-ref'


# Load proxy settings from environment variables
proxies = {
    'http': os.getenv('HTTP_PROXY'),
    'https': os.getenv('HTTPS_PROXY')
}
response = requests.post(url, json= data, headers=headers, proxies=proxies, timeout=10)

# Check the response status
if response.status_code == 200:
    # Successful response
    data = response.json()
    ref_num = data.get('data', {}).get('refnum')  # Adjust the key here
    if ref_num and ref_num.endswith('-SKIP'):
        trimmed_ref_num = ref_num[:-2]  # Remove the '-SKIP' suffix
        print("Success! The trimmed code is:", trimmed_ref_num)
    else:
        print("Success! The code is:", ref_num)
elif response.status_code == 404:
    # Not Found response
    print("There is no code.")
else:
    # Other error occurred
    print("Error:", response.status_code, response.text)
