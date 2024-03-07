from flask import Flask ,jsonify , request
import requests



app = Flask(__name__)

base_url = "https://api.openai.com/v1/"
api_key = "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"
assistant_id = "asst_onq8ERkgkhL7jI5tXYayLRsq"

def status_update(thread_id, run_id, headers):
    # Get response for the first URL
    url = base_url + "threads/" + thread_id + "/runs/" + run_id
    response = requests.get(url, headers=headers)
    response_json = response.json()

    # Get response for the second URL
    url = base_url + "threads/" + thread_id + "/runs/" + run_id + "/steps"
    response_json = requests.get(url, headers=headers).json()

    # Extract status
    status = response_json.get("data")[0]['status'] == "completed"
    return status

def check_status(thread_id, run_id, headers,msg_id):


    while True:
        # Make requests to check status
        status = status_update(thread_id, run_id, headers)
        
        if status:
            # If status is True, fetch the response
            url = base_url + "threads/" + thread_id + "/messages?before=" + msg_id + "&limit=10"
            ans = requests.get(url, headers=headers).json()
            text_values = []
            for item in ans['data']:
                if item['content']:  # Check if content is not empty
                    text_values.append(item['content'][0]['text']['value'])
            return jsonify(text_values,"NEXT IS FOR TESTING",ans)
        
def generate_headers(api_key):
    headers = {
        "Authorization": "Bearer " + api_key,
        "OpenAI-Beta": "assistants=v1"
    }
    return headers




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

@app.route("/query",methods=["POST"])
def query():
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

    if response_json.get('data') and response_json.get('data')[0]['content']:
        ans = response_json.get("data")[0]['content'][0]['text']['value']
        return jsonify(ans)
    else:
        # Call the function to check status repeatedly
        return check_status(thread_id, run_id, headers,msg_id)
        

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5050)









