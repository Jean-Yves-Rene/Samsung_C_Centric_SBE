from flask import Flask,render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
from sg_ccentric import check_code_c_centric
from waitress import serve
from datetime import datetime
from dotenv import load_dotenv
import logging
import secrets
import os
from pymongo import MongoClient, errors

# Load environment variables from .env file
load_dotenv()

# Access environment variables
mongodb_username = os.getenv('MONGODB_USERNAME')
mongodb_password = os.getenv('MONGODB_PASSWORD')
mongodb_ip = os.getenv('MONGODB_IP')
mongodb_auth_source = os.getenv('MONGODB_AUTH_SOURCE')
# Environment variables for credentials
usernamestored = os.getenv('USERNAMELOGIN')
passwordstored = os.getenv('PASSWORD')  



app = Flask(__name__)

# Secret key for session management
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'mysecretkeyccentric2024?>')


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

# Login decorator to protect routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))  # Redirect to login if session expired
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Home route
@app.route('/')
#@app.route('/login')
def home():
    return render_template ('login.html')  # Redirect to login

# Login route with rate limiting
@app.route('/login', methods=['GET', 'POST'])
#@limiter.limit("5 per minute")  # Specific rate limit for login
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
             
        if not password:
            logging.error("Environment variable 'PASSWORD' is not set.")
            return "Server misconfiguration. Please contact the administrator.", 500

        # Validate credentials
        try:
            if username == usernamestored and password == passwordstored:
                session['username'] = username
                session.permanent = True  # Enable session timeout
                logging.info(f"User {username} logged in successfully.")
                return render_template('index.html', username = username)
            else:
                logging.warning(f"Failed login attempt for username: {username}")
                return render_template('errorlogin.html', error="Invalid credentials.")
        except Exception as e:
            logging.error(f"Login error: {e}")
            return "An error occurred during login. Please try again later.", 500

    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    session.clear()  # Clear the entire session
    session.pop('username', None)
    logging.info("User logged out.")
    return redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    username = session.get('username')  # Get username from session
    if not username:
        flash("Session expired. Please log in again.", "danger")
        return redirect(url_for('login'))
    else:
        return render_template('index.html', username=session['username'])

@app.route('/ccentric')
@login_required
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