from flask import Flask, render_template, request
from sg_ccentric import check_code_c_centric
from waitress import serve
from datetime import datetime
from dotenv import load_dotenv
import os
from pymongo import MongoClient, errors

# Load environment variables from .env file
load_dotenv()

# Access environment variables
mongodb_username = os.getenv('MONGODB_USERNAME')
mongodb_password = os.getenv('MONGODB_PASSWORD')
mongodb_ip = os.getenv('MONGODB_IP')
mongodb_auth_source = os.getenv('MONGODB_AUTH_SOURCE')

app = Flask(__name__)

# Construct the MongoDB URI using the loaded environment variables
uri = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_ip}/?authSource={mongodb_auth_source}"
client = None

try:
    client = MongoClient(uri)
    # Check if connection is successful
    db_names = client.list_database_names()
    print("Connected to MongoDB")
    print("Available databases:")
    for db_name in db_names:
        print(db_name)
except errors.ConnectionFailure as e:
    print("Could not connect to MongoDB:", e)
    client = None

collection = None
if client:
    db = client["local"]  # Replace with your actual database name
    collection = db["Imeis_C_Centric"]  # Replace with your actual collection name
else:
    collection = None # Ensure collection is None if client isn't connected

# Function to get current date and time
def get_current_date():
    return datetime.now()

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

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
        if client is not None and collection is not None:
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
            return render_template("error.html", error="MongoDB client is not connected.")
                      
    else:
        return render_template("invalid_imei.html")

#Gracefully disconnect from MongoDB when the application exits
# @app.teardown_appcontext
# def close_connection(exception):
#     if client:
#         client.close()

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)