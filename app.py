from flask import Flask, request, jsonify
import requests
import os
import logging
from dotenv import load_dotenv
import time
import json

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a console handler for detailed request/response logging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Create a separate logger for request/response details
request_logger = logging.getLogger('request_logger')
request_logger.setLevel(logging.DEBUG)
request_logger.addHandler(console_handler)
request_logger.propagate = False  # Don't propagate to parent logger

app = Flask(__name__)

# Get Databricks token from environment variables
DATABRICKS_TOKEN = os.environ.get('DATABRICKS_TOKEN')
if not DATABRICKS_TOKEN:
    logger.warning("DATABRICKS_TOKEN environment variable not set")

# Base URL for Databricks API
BASE_URL = os.environ.get('DATABRICKS_BASE_URL', 
                        "https://dbc-dc8dabd2-571d.cloud.databricks.com/serving-endpoints")

# Model configurations
DEFAULT_MODEL = "databricks-meta-llama-3-1-405b-instruct"
AVAILABLE_MODELS = os.environ.get('AVAILABLE_MODELS', DEFAULT_MODEL).split(',')

# Configuration object for future flexibility
CONFIG = {
    "models": {model_id: {"id": model_id, "object": "model", "owned_by": "organization_owner"} 
               for model_id in AVAILABLE_MODELS}
}

@app.route('/v1/models', methods=['GET'])
def get_models():
    """Return a list of available models."""
    logger.info("GET request to /v1/models")
    request_logger.debug(f"GET /v1/models - Headers: {dict(request.headers)}")
    models_data = [CONFIG["models"][model_id] for model_id in CONFIG["models"]]
    return jsonify({
        "data": models_data,
        "object": "list"
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Handle chat completion requests."""
    data = request.json
    logger.info(f"POST request to /v1/chat/completions with model: {data.get('model', DEFAULT_MODEL)}")
    
    # Log detailed request information
    request_logger.debug(f"INCOMING REQUEST - POST /v1/chat/completions")
    request_logger.debug(f"Request Headers: {dict(request.headers)}")
    request_logger.debug(f"Request Body: {json.dumps(data, indent=2)}")
    
    # Extract model ID from request or use default
    model_id = data.get('model', DEFAULT_MODEL)
    
    # Validate model exists in our configuration
    if model_id not in CONFIG["models"]:
        return jsonify({"error": f"Model {model_id} not found"}), 404
    
    # Format the request for Databricks API
    # The key aspect here is formatting the request correctly for Databricks
    messages = data.get("messages", [])
    
    # Process messages to ensure content is a string (Databricks requirement)
    processed_messages = []
    for msg in messages:
        msg_copy = msg.copy()
        # If content is an array, convert it to a string
        if isinstance(msg_copy.get("content"), list):
            # Extract text content from array items
            text_content = []
            for item in msg_copy["content"]:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_content.append(item.get("text", ""))
            msg_copy["content"] = "\n".join(text_content)
        processed_messages.append(msg_copy)
        
    temperature = data.get('temperature', 0.7)
    top_p = data.get('top_p', 1.0)
    stop_sequences = data.get('stop', [])
    
    databricks_request = {
        "model": model_id,
        "max_tokens": data.get("max_tokens", 2048),
        "temperature": temperature,
        "top_p": top_p,
        "stop": stop_sequences,
    }
    
    # Make the request to Databricks API
    try:
        # Log outgoing request to Databricks
        # Add processed messages to the request
        
        databricks_request["messages"] = processed_messages
        
        request_logger.debug(f"OUTGOING REQUEST - POST {BASE_URL}/{model_id}/invocations")
        request_logger.debug(f"Outgoing Headers: {{'Authorization': 'Bearer [REDACTED]'}}")
        request_logger.debug(f"Outgoing Body: {json.dumps(databricks_request, indent=2)}")
        response = requests.post(
            f"{BASE_URL}/{model_id}/invocations",
            headers={"Authorization": f"Bearer {DATABRICKS_TOKEN}"},
            json=databricks_request,
            timeout=120
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Log response from Databricks
        request_logger.debug(f"RESPONSE from Databricks - Status Code: {response.status_code}")
        request_logger.debug(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        # Return the response in OpenAI format
        # Transform Databricks response to OpenAI format
        databricks_response = response.json()
        
        # Transform Databricks response to OpenAI format
        # This is a simplified version and may need adjustments
        openai_format_response = {
            "id": f"chatcmpl-{databricks_response.get('id', 'unknown')}",
            "object": "chat.completion",
            "created": databricks_response.get("created", int(time.time())),
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": databricks_response.get("choices", [{}])[0].get("message", {}).get("content", "")
                    },
                    "finish_reason": databricks_response.get("choices", [{}])[0].get("finish_reason", "stop")
                }
            ],
            "usage": databricks_response.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
        }
        
        return jsonify(openai_format_response)
    
    except requests.exceptions.RequestException as e:
        # Log error response
        request_logger.error(f"ERROR in request to Databricks: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            request_logger.error(f"Error Response Body: {e.response.text}")
        logger.error(f"Error making request to Databricks API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/v1/completions', methods=['POST'])
def completions():
    """Handle standard completion requests."""
    data = request.json
    logger.info(f"POST request to /v1/completions with model: {data.get('model', DEFAULT_MODEL)}")
    
    # Log detailed request information
    request_logger.debug(f"INCOMING REQUEST - POST /v1/completions")
    request_logger.debug(f"Request Headers: {dict(request.headers)}")
    request_logger.debug(f"Request Body: {json.dumps(data, indent=2)}")
    
    # Extract model ID from request or use default
    model_id = data.get('model', DEFAULT_MODEL)
    
    # Validate model exists in our configuration
    if model_id not in CONFIG["models"]:
        return jsonify({"error": f"Model {model_id} not found"}), 404
    
    # For completion endpoint, convert to a format that the chat model can understand
    # This is necessary because many LLM models now prefer the chat format
    prompt = data.get("prompt", "")
    
    # Create a messages array with a single user message containing the prompt
    # Handle case where prompt might be an array
    if isinstance(prompt, list):
        text_content = []
        for item in prompt:
            if isinstance(item, dict) and item.get("type") == "text":
                text_content.append(item.get("text", ""))
        prompt_text = "\n".join(text_content)
    else:
        prompt_text = prompt
    
    messages = [{"role": "user", "content": prompt_text}]
    
    temperature = data.get('temperature', 0.7)
    top_p = data.get('top_p', 1.0)
    stop_sequences = data.get('stop', [])
    
    # Format the request for Databricks API
    databricks_request = {
        "messages": messages, 
        "model": model_id, 
        "max_tokens": data.get("max_tokens", 256)
    }
    
    # Make the request to Databricks API
    try:
        # Log outgoing request to Databricks
        request_logger.debug(f"OUTGOING REQUEST - POST {BASE_URL}/{model_id}/invocations")
        request_logger.debug(f"Outgoing Headers: {{'Authorization': 'Bearer [REDACTED]'}}")
        request_logger.debug(f"Outgoing Body: {json.dumps(databricks_request, indent=2)}")
        response = requests.post(
            f"{BASE_URL}/{model_id}/invocations",
            headers={"Authorization": f"Bearer {DATABRICKS_TOKEN}"},
            json=databricks_request,
            timeout=120
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Log response from Databricks
        request_logger.debug(f"RESPONSE from Databricks - Status Code: {response.status_code}")
        request_logger.debug(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        # Return the response in OpenAI format
        databricks_response = response.json()
        
        # Transform to completions format (different from chat.completions)
        openai_format_response = {
            "id": f"cmpl-{databricks_response.get('id', 'unknown')}",
            "object": "text_completion",
            "created": databricks_response.get("created", int(time.time())),
            "model": model_id,
            "choices": [
                {
                    "text": databricks_response.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": databricks_response.get("choices", [{}])[0].get("finish_reason", "stop")
                }
            ],
            "usage": databricks_response.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
        }
        
        return jsonify(openai_format_response)
    
    except requests.exceptions.RequestException as e:
        # Log error response
        request_logger.error(f"ERROR in request to Databricks: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            request_logger.error(f"Error Response Body: {e.response.text}")
        logger.error(f"Error making request to Databricks API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/v1/embeddings', methods=['POST'])
def embeddings():
    """Handle embedding requests."""
    data = request.json
    logger.info(f"POST request to /v1/embeddings with model: {data.get('model', DEFAULT_MODEL)}")
    
    # Log detailed request information
    request_logger.debug(f"INCOMING REQUEST - POST /v1/embeddings")
    request_logger.debug(f"Request Headers: {dict(request.headers)}")
    request_logger.debug(f"Request Body: {json.dumps(data, indent=2)}")
    
    # Currently, this is a simple passthrough to the Databricks API
    # In a real implementation, you'd need to adjust this based on the
    # actual Databricks embedding endpoint and its requirements
    
    model_id = data.get('model', DEFAULT_MODEL)
    
    # Format the request for Databricks API
    databricks_request = {
        "input": data.get("input", ""),
        "model": model_id
    }
    
    # For now, this is a placeholder response since the embedding functionality
    # is less important as mentioned in the original task
    return jsonify({
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [0.0] * 1536,  # Placeholder
                "index": 0
            }
        ],
        "model": model_id,
        "usage": {
            "prompt_tokens": 0,
            "total_tokens": 0
        }
    })

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    """Simple health check endpoint."""
    request_logger.debug(f"GET /healthcheck - Headers: {dict(request.headers)}")
    return jsonify({"status": "ok"})

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Load additional configuration if needed
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting API server on port {port}, debug={debug}")
    request_logger.info(f"Detailed request logging enabled to console output")
    app.run(host='0.0.0.0', port=port, debug=debug)
