from flask import Flask,render_template, request, jsonify, session, redirect, url_for, flash
from sg_ccentric import check_code_c_centric
from waitress import serve
from datetime import datetime
from dotenv import load_dotenv
import logging
import os
from pymongo import MongoClient, errors

# Load environment variables from .env file
load_dotenv()

# Access environment variables
mongodb_username = os.getenv('MONGODB_USERNAME')
mongodb_password = os.getenv('MONGODB_PASSWORD')
mongodb_ip = os.getenv('MONGODB_IP')
mongodb_auth_source = os.getenv('MONGODB_AUTH_SOURCE')
# Read variables from .env
host = os.getenv("HOST")  
port = int(os.getenv("PORT"))    

app = Flask(__name__)

# Construct the MongoDB URI using the loaded environment variables
uri = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_ip}/?authSource={mongodb_auth_source}"

# Secret key for session management
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'mysecretkeyccentric2024?>')

# Initialize MongoClient once for the application
mongo_client = MongoClient(uri)
db = mongo_client["local"]  # Replace with your database name
collection = db["Imeis_C_Centric"]  # Replace with your collection name

# Function to get current date and time
def get_current_date():
    return datetime.now()

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Home route
@app.route('/')
def home():
    return render_template ('index.html')  # Redirect to login

@app.route('/ccentric')
def get_code():
    imei = request.args.get('imei', '')
    # Check if the IMEI is a numeric value and has a length of 15
    if imei.isdigit() and len(imei) == 15:
        result_code_c_centric = check_code_c_centric(imei)
        # Add current date to the data
        current_date = get_current_date().strftime("%Y-%m-%dT%H:%M")
        data = {
            "imei": imei,
            "result": result_code_c_centric,
            "date_added": current_date  # Add date field
        }
        # Insert IMEI into MongoDB collection if client is connected
        try:
            collection.insert_one(data)
            return render_template(
                "ccentric.html",
                imei=imei,  # Pass imei to the template
                result=result_code_c_centric
            )
        except errors.PyMongoError as e:
            print(f"Failed to insert data into MongoDB: {e}")
            return render_template("error.html", error="Database insertion failed.")
    else:
        return render_template("invalid_imei.html")

#Gracefully disconnect from MongoDB when the application exits
# @app.teardown_appcontext
# def close_mongo_connection(exception):
#     if mongo_client:
#         mongo_client.close()

if __name__ == "__main__":
    serve(app, host=host, port=port)