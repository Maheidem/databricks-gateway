#!/usr/bin/env python3
"""
A simple test script for the Databricks Gateway API wrapper.
This script tests the main functionality of the wrapper.
"""

import requests
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Base URL for the API
BASE_URL = "http://localhost:5001/v1"

def print_section(title):
    """Print a section title with formatting"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def pretty_print_json(data):
    """Print JSON data with indentation"""
    print(json.dumps(data, indent=2))

def test_healthcheck():
    """Test the healthcheck endpoint"""
    print_section("Testing Healthcheck Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL.replace('/v1', '')}/healthcheck")
        print(f"Status Code: {response.status_code}")
        pretty_print_json(response.json())
        
        if response.status_code == 200 and response.json().get("status") == "ok":
            print("\n✅ Healthcheck test passed!")
        else:
            print("\n❌ Healthcheck test failed!")
        
    except Exception as e:
        print(f"\n❌ Error connecting to server: {str(e)}")
        print("Make sure the server is running at the specified URL.")

def test_models_endpoint():
    """Test the models endpoint"""
    print_section("Testing Models Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/models")
        print(f"Status Code: {response.status_code}")
        pretty_print_json(response.json())
        
        if response.status_code == 200 and response.json().get("data"):
            print("\n✅ Models endpoint test passed!")
        else:
            print("\n❌ Models endpoint test failed!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

def test_chat_completions():
    """Test the chat completions endpoint"""
    print_section("Testing Chat Completions Endpoint")
    
    try:
        # Get the first model from the list
        models_response = requests.get(f"{BASE_URL}/models")
        models = models_response.json().get("data", [])
        
        if not models:
            print("❌ No models available to test with!")
            return
        
        model_id = models[0]["id"]
        print(f"Using model: {model_id}")
        
        # Simple chat completion request
        request_data = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Hello, how are you today?"}
            ],
            "max_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        print("\nRequest:")
        pretty_print_json(request_data)
        
        response = requests.post(
            f"{BASE_URL}/chat/completions", 
            json=request_data
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print("Response:")
        pretty_print_json(response.json())
        
        if response.status_code == 200:
            print("\n✅ Chat completions test passed!")
        else:
            print("\n❌ Chat completions test failed!")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

def test_completions():
    """Test the completions endpoint"""
    print_section("Testing Completions Endpoint")
    
    try:
        # Get the first model from the list
        models_response = requests.get(f"{BASE_URL}/models")
        models = models_response.json().get("data", [])
        
        if not models:
            print("❌ No models available to test with!")
            return
        
        model_id = models[0]["id"]
        print(f"Using model: {model_id}")
        
        # Simple completion request
        request_data = {
            "model": model_id,
            "prompt": "Complete this sentence: The quick brown fox",
            "max_tokens": 100,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        print("\nRequest:")
        pretty_print_json(request_data)
        
        response = requests.post(
            f"{BASE_URL}/completions", 
            json=request_data
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print("Response:")
        pretty_print_json(response.json())
        
        if response.status_code == 200:
            print("\n✅ Completions test passed!")
        else:
            print("\n❌ Completions test failed!")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

def main():
    """Run all tests"""
    print("Starting Databricks Gateway API Tests")
    print(f"Base URL: {BASE_URL}")
    
    test_healthcheck()
    test_models_endpoint()
    test_chat_completions()
    test_completions()
    
    print_section("Test Summary")
    print("All tests completed! Check the results above for any failures.")
    print("If everything passed, your Databricks Gateway API wrapper is working correctly!")

if __name__ == "__main__":
    main()