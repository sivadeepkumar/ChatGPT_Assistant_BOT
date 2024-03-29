from flask import Flask ,jsonify , request
import requests
import logging

from flask_cors import CORS
import traceback
app = Flask(__name__)
CORS(app)
import re 
from dotenv import load_dotenv
import os 
load_dotenv()
api_key = os.getenv("API_KEY")

logging.basicConfig(level=logging.DEBUG,
                    handlers=[logging.FileHandler('app.log', mode='a')],
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger(__name__)

base_url = "https://api.openai.com/v1/"
assistant_id = "asst_onq8ERkgkhL7jI5tXYayLRsq"

def convert_backticks(text):
    count = 0
    while '```' in text:
        if count % 2 == 0:
            text = re.sub(r'```', '<$>', text, count=1)
        else:
            text = re.sub(r'```', '<^>', text, count=1)
        count += 1
    return text

def get_first_url_response(thread_id, run_id, headers):
    # Log usage
    logger.info("Getting response for the first URL...")

    # Construct the URL
    url = base_url + "threads/" + thread_id + "/runs/" + run_id

    # Make request to the URL and parse JSON response
    response = requests.get(url, headers=headers)
    response_json = response.json()

    return response_json

def get_second_url_response(thread_id, run_id, headers):
    # Log usage
    logger.info("Getting response for the second URL...")

    # Construct the second URL
    url = base_url + "threads/" + thread_id + "/runs/" + run_id + "/steps"

    # Make request to the second URL and parse JSON response
    response_json = requests.get(url, headers=headers).json()

    return response_json



def status_update(thread_id, run_id, headers):
    # Log usage
    logger.info("Checking status...")

    first_response_json = get_first_url_response(thread_id, run_id, headers)

    second_response_json = get_second_url_response(thread_id, run_id, headers)

    if second_response_json.get("data"):
        # Extract status if there are elements in the list
        status = second_response_json.get("data")[0]['status'] == "completed"
        return status
    else:
        # Handle the case where the list is empty (no data returned)
        logger.error("No data returned in response")
        return False




def check_status(thread_id, run_id, headers,msg_id):
    # Log usage
    logger.info("Checking status repeatedly...")

    while True:  
        # Make requests to check status
        status = status_update(thread_id, run_id, headers)
        
        if status:
            # Log usage
            logger.info("Status is true. Fetching response...")

            # If status is True, fetch the response
            url = base_url + "threads/" + thread_id + "/messages?before=" + msg_id + "&limit=10"
            ans = requests.get(url, headers=headers).json()
            text_values = []
            text_values_converted = {}

            count = 0
            for item in ans['data']:
                
                if item['content']:  # Check if content is not empty
                    key = "key_" + str(count)
                    count += 1
                    text_values.append(item['content'][0]['text']['value'])

            

            return jsonify(text_values)                              #  ,"               *****************************         BELOW ONE IS FOR TESTING PURPOSE ONLY, PLEASE DON'T CARE THIS INFORMATION.THANKYOU               ************************",ans)






def get_messages_before(base_url, thread_id, msg_id, limit, headers):
    url = f"{base_url}threads/{thread_id}/messages?before={msg_id}&limit={limit}"
    response = requests.get(url, headers=headers)
    response_json = response.json()
    return response_json

def create_run(base_url, thread_id, assistant_id, headers):
    url = base_url + f"threads/{thread_id}/runs"
    body = {
        "assistant_id": assistant_id
    }
    response = requests.post(url, headers=headers, json=body)
    run_id = response.json().get("id")
    return run_id

def create_message(base_url, thread_id, headers, query):
    url = base_url + f"threads/{thread_id}/messages"
    body = {
        "role": "user",
        "content": query
    }
    response = requests.post(url, headers=headers, json=body)
    response_json = response.json()
    msg_id = response_json.get('id')
    return msg_id

def create_thread(base_url, headers):
    url = base_url + "threads"
    response = requests.post(url, headers=headers)
    response_json = response.json()
    thread_id = response_json.get('id')
    return thread_id

def generate_headers(api_key):
    headers = {
        "Authorization": "Bearer " + api_key,
        "OpenAI-Beta": "assistants=v1"
    }
    return headers

@app.route("/query",methods=["POST"])
def query():
    try:
        data = request.get_json()
        query = data['query']
        
        # headers payload
        headers = generate_headers(api_key)

        # Create a thread
        thread_id = create_thread(base_url, headers)

        # Create a message in the thread
        msg_id = create_message(base_url, thread_id, headers, query)

        # Create a run in the thread
        run_id = create_run(base_url, thread_id, assistant_id, headers)

        # Get messages before a specific message ID with a limit of 10
        response_json = get_messages_before(base_url, thread_id, msg_id, 10, headers)

        
        # if response_json.get('data') and response_json.get('data')[0]['content']:
        #     text_values = response_json.get("data")[0]['content'][0]['text']['value']
        #     logger.info(f"first_ans: {text_values}")
        #     return jsonify([text_values])
        # else:
        #     # Call the function to check status repeatedly
        return check_status(thread_id, run_id, headers,msg_id)
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        traceback.print_exc()  # Print the traceback to console
        logger.exception("Exception occurred", exc_info=True)  # Log the exception with full traceback
        return "An error occurred. Please check the logs for more details."

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5055)

