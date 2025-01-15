from flask import Flask, request, jsonify
from UserManagerAPI import create_user, get_user
import requests
from jwt_manager import *

USER_MANAGER_API_URL = "http://localhost:6000"

app = Flask(__name__)

# Check both profile for predator,
# return true if one of the profiles is a predator
# check Report Manager for the profiles info, and LLM Manager for info from the messages
@app.route('/check_for_predator', methods=['POST'])
def check_for_predator():
    return jsonify({"message": "check_for_predator"}), 200


# Get the report from the user and save it to the db with the status -1 (under review)
@app.route('/submit_report', methods=['POST'])
def submit_report():
    return jsonify({"message": "submit_report"}), 200


# New User - ask sign-up request from User Manger
@app.route("/sign-up", methods=["POST"])
def sign_up():
    data = request.get_json()
    if not data:
         return jsonify({'eror':'No input data provided'}),400
    
    response = requests.post(f"""{USER_MANAGER_API_URL}/users""", json=data)
    
    if response.status_code != 200:
        return jsonify(response.json()), response.status_code
    
    username = response.json().get('username')
    token = generate_jwt(username)

    return jsonify({"message": "User signed up successfully", "token": token}), response.status_code 


# Existing User - ask sign-in request from User Manger
@app.route("/sign-in", methods=["POST"])
def sign_in():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    response = requests.post(f"{USER_MANAGER_API_URL}/authenticate", json=data)

    if response.status_code != 200:
        return response.json(), response.status_code

    username = response.json().get('username')
    token = generate_jwt(username)

    return jsonify({"message": "User signed in successfully", "token": token}), 200



# הרצת ה-Orchestrator
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=7000)




