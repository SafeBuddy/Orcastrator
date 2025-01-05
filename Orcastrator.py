
from flask import Flask, request, jsonify
# import requests

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
   return jsonify({"message": "User signed up successfully"}), 200


# Existing User - ask sign-in request from User Manger
@app.route("/sign-in", methods=["POST"])
def sign_in():
    return jsonify({"message": "User signed in successfully"}), 200


# הרצת ה-Orchestrator
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)




