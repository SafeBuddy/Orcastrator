from flask import Flask, request, jsonify
from UserManagerAPI import create_user, get_user
import requests
from jwt_manager import *

USER_MANAGER_API_URL = "http://localhost:6000"
LLM_MANAGER_URL = "http://localhost:5001"
REPORT_MANAGER_URL ="http://localhost:5000"
ALERT_MANAGER_URL = "http://localhost:5005"

app = Flask(__name__)

def get_email_of_parent(username):
    try:
        user_response = requests.get(f"{USER_MANAGER_API_URL}/users/{username}") 
        if user_response.status_code == 200:
            user_data = user_response.json()
            email = user_data.get("p_contact")  
            return email
        else:
            print(f"Failed to fetch data for user {username}. Status code: {user_response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return None

# Send alert to Alert Manager
def send_alert(email, profile):
    alert_data = {
        "user_name": profile,
        "parent_email": email
    }
    try:
        response = requests.post(f"{ALERT_MANAGER_URL}/alert-parent", json=alert_data)
        if response.status_code == 200:
            print(f"Alert sent successfully to {email}.")
        else:
            print(f"Failed to send alert to {email}: {response.text}")
    except Exception as e:
        print(f"Error sending alert: {e}")
        
# Check both profile for predator,
# return true if one of the profiles is a predator
# check Report Manager for the profiles info, and LLM Manager for info from the messages
# Step 1: Check if any participant has a risk_level of 2 - dangerous
# Step 2: If no suspicious users with risk_level 2 are found, proceed with LLM analysis
# Step 3: Process the analysis data and update risk levels
@app.route('/check_for_predator', methods=['POST'])
def check_for_predator():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    participants = data.get('participants', [])
    if not participants:
        return jsonify({"error": "No participants provided"}), 400

    
    for participant in participants:
        report_response = requests.get(f"{REPORT_MANAGER_URL}/reports/{participant}")
        if report_response.status_code == 200:
            report_data = report_response.json()
            risk_level = report_data.get("risk_level")
            
            if risk_level == 2:
                other_participant = participants[0] if participants[1] == participant else participants[1]
                print(other_participant)
                email = get_email_of_parent(other_participant)  
                
                if email:
                    send_alert(email,other_participant)
                    return jsonify({
                        "message": "You are interacting with a suspicious user",
                        "suspicious_profile": participant,
                        "risk_level": risk_level
                    }), 200
                
            elif risk_level == 1:
                other_participant = participants[0] if participants[1] == participant else participants[1]
                return jsonify({
                    "message": f"User {other_participant} is interacting with a low-risk user",
                    "profile": other_participant,
                    "risk_level": 1
                }), 200
        #elif report_response.status_code == 404:
            # If no report exists for the participant, continue to the next one
            #continue
        #else:
            # Handle unexpected errors from the Report Manager
            #return jsonify({"error": f"Failed to fetch report for participant {participant}"}), report_response.status_code
    
    
    messages = data.get('messages', [])
    if not messages:
        return jsonify({"error": "No messages provided for analysis"}), 400

    llm_response = requests.post(f"{LLM_MANAGER_URL}/check-messages", json={"messages": messages})
    if llm_response.status_code != 200:
        print(f"LLM Manager failed with status {llm_response.status_code}: {llm_response.text}")
        return jsonify({"error": "LLM Manager analysis failed"}), llm_response.status_code
    print(llm_response.json())
    llm_data = llm_response.json()
    
    
    aggressor = llm_data.get("aggressor")
    severity_score = llm_data.get("severity")

    if aggressor and severity_score:
        if severity_score == 2:
            other_participant = participants[0] if participants[1] == aggressor else participants[1]
            email = get_email_of_parent(other_participant)
            
            if email:
                send_alert(email, aggressor)  
                
        elif severity_score == 1:
            other_participant = participants[0] if participants[1] == aggressor else participants[1]
            return jsonify({
                "message": f"You are interacting with a medium-risk user ({other_participant})",
                "aggressor": aggressor,
                "severity": severity_score
            }), 200
        else:
            return jsonify({
                "error": "No risk detected.",
                "aggressor": aggressor,
                "severity": severity_score
            }), 400

        report_response = requests.get(f"{REPORT_MANAGER_URL}/reports/{aggressor}")
        if report_response.status_code == 200:
            current_report = report_response.json()
            current_risk_level = current_report.get("risk_level")

            if severity_score > current_risk_level:
                update_response = requests.put(
                    f"{REPORT_MANAGER_URL}/reports/{aggressor}",
                    json={"risk_level": severity_score}
                )
                if update_response.status_code != 200:
                    return jsonify({
                        "error": f"Failed to update risk level for profile {aggressor}"
                    }), update_response.status_code
        elif report_response.status_code == 404:
            create_response = requests.post(
                f"{REPORT_MANAGER_URL}/reports",
                json={"risk_profile": aggressor, "risk_level": severity_score}
            )
            if create_response.status_code != 201:
                return jsonify({
                    "error": f"Failed to create report for profile {aggressor}"
                }), create_response.status_code

    return jsonify({
        "message": "LLM analysis completed",
        "aggressor": aggressor,
        "severity": severity_score
    }), 200

# Get the report from the user and save it to the db 
# Sending requests to Report Manager to create new report
@app.route('/submit_report', methods=['POST'])
def submit_report():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request"}), 400
    
    response = requests.post(f"{REPORT_MANAGER_URL}/reports", json=data)
    #return jsonify(response.json()), response.status_code
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



# Run Orchestrator
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=7000)




