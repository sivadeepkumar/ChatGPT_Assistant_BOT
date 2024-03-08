from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import requests
import logging
import markdown
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

base_url = "https://api.openai.com/v1/"
api_key = "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"
assistant_id = "asst_onq8ERkgkhL7jI5tXYayLRsq"

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

    # Extract status
    status = second_response_json.get("data")[0]['status'] == "completed"
    return status

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

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('query')
def handle_query(data):
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

    if response_json.get('data') and response_json.get('data')[0]['content']:
        text_values = response_json.get("data")[0]['content'][0]['text']['value']
        logger.info(f"first_ans: {text_values}")
        emit('response', markdown.markdown(text_values))
    else:
        # Call the function to check status repeatedly
        while True:
            status = status_update(thread_id, run_id, headers)
            if status:
                logger.info("Status is true. Fetching response...")
                url = base_url + "threads/" + thread_id + "/messages?before=" + msg_id + "&limit=10"
                ans = requests.get(url, headers=headers).json()
                for item in ans['data']:
                    if item['content']:
                        emit('response', item['content'][0]['text']['value'])
                break

if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5005)