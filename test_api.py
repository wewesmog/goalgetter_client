#!/usr/bin/env python3
"""
Simple test script for the Goalgetter API.

This script demonstrates how to use the simplified API endpoints.
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_chat():
    """Test the chat endpoint."""
    print("💬 Testing chat endpoint...")
    
    # Simple chat request - only message and user_id required
    chat_data = {
        "message": "Hello! Can you help me set up a goal to learn Python?",
        "user_id": "123"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_memory():
    """Test the memory endpoint."""
    print("🧠 Testing memory endpoint...")
    
    # Check memory for user
    user_id = "123"
    response = requests.get(f"{BASE_URL}/memory/{user_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_conversation():
    """Test a conversation flow."""
    print("🔄 Testing conversation flow...")
    
    user_id = "456"
    
    # First message
    print("📝 First message:")
    chat_data = {
        "message": "I want to create a goal to exercise 3 times a week",
        "user_id": user_id
    }
    response = requests.post(f"{BASE_URL}/chat", json=chat_data)
    print(f"Response: {response.json()['message']}")
    print()
    
    # Second message (should have context)
    print("📝 Second message:")
    chat_data = {
        "message": "What should I do to track my progress?",
        "user_id": user_id
    }
    response = requests.post(f"{BASE_URL}/chat", json=chat_data)
    print(f"Response: {response.json()['message']}")
    print()
    
    # Check memory
    print("🧠 Memory status:")
    response = requests.get(f"{BASE_URL}/memory/{user_id}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

if __name__ == "__main__":
    print("🚀 Testing Goalgetter API")
    print("=" * 50)
    
    try:
        test_health()
        test_chat()
        test_memory()
        test_conversation()
        
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

