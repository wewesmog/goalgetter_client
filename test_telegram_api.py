#!/usr/bin/env python3
"""
Test script for the Telegram API format.

This script demonstrates how to use the API with Telegram user data.
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_telegram_chat():
    """Test the chat endpoint with Telegram user data."""
    print("📱 Testing Telegram chat endpoint...")
    
    # Telegram user data (simulating what Telegram sends)
    telegram_user = {
        "id": 123456789,
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "language_code": "en",
        "is_bot": False,
        "is_premium": True
    }
    
    # Chat request with Telegram format
    chat_data = {
        "message": "Hello! Can you help me set up a goal to learn Python?",
        "user": telegram_user,
        "chat_id": 123456789,
        "message_id": 1
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_telegram_user_creation():
    """Test user creation with different Telegram users."""
    print("👥 Testing Telegram user creation...")
    
    # Test with different users
    users = [
        {
            "id": 111111111,
            "first_name": "Alice",
            "last_name": "Smith",
            "username": "alice_smith",
            "language_code": "en",
            "is_bot": False,
            "is_premium": False
        },
        {
            "id": 222222222,
            "first_name": "Bob",
            "last_name": None,
            "username": None,
            "language_code": "es",
            "is_bot": False,
            "is_premium": True
        },
        {
            "id": 333333333,
            "first_name": "Charlie",
            "last_name": "Brown",
            "username": "charlie_brown",
            "language_code": "fr",
            "is_bot": False,
            "is_premium": False
        }
    ]
    
    for i, user in enumerate(users, 1):
        print(f"📝 Testing user {i}: {user['first_name']} (@{user['username'] or 'no_username'})")
        
        chat_data = {
            "message": f"Hi! I'm {user['first_name']}. Can you help me create a goal?",
            "user": user,
            "chat_id": user["id"],
            "message_id": i
        }
        
        response = requests.post(f"{BASE_URL}/chat", json=chat_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()["data"]
            print(f"User ID: {data['user_id']}")
            print(f"User Name: {data['user_name']}")
            print(f"Username: @{data['username'] or 'N/A'}")
            print(f"Language: {data['language_code'] or 'N/A'}")
            print(f"Chat ID: {data['chat_id']}")
        else:
            print(f"Error: {response.text}")
        print()

def test_conversation_flow():
    """Test conversation flow with the same user."""
    print("🔄 Testing conversation flow...")
    
    user = {
        "id": 444444444,
        "first_name": "David",
        "last_name": "Wilson",
        "username": "david_wilson",
        "language_code": "en",
        "is_bot": False,
        "is_premium": False
    }
    
    messages = [
        "Hello! I want to create a goal to exercise 3 times a week",
        "What should I do to track my progress?",
        "Can you show me my goals?",
        "I completed my workout today, can you log that?"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"📝 Message {i}: {message}")
        
        chat_data = {
            "message": message,
            "user": user,
            "chat_id": user["id"],
            "message_id": i
        }
        
        response = requests.post(f"{BASE_URL}/chat", json=chat_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['message'][:100]}...")
            print(f"Message count in history: {data['data'].get('message_count', 'N/A')}")
        else:
            print(f"Error: {response.text}")
        print()

def test_memory_endpoint():
    """Test memory endpoint with Telegram user ID."""
    print("🧠 Testing memory endpoint...")
    
    user_id = "123456789"  # Telegram user ID as string
    response = requests.get(f"{BASE_URL}/memory/{user_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

if __name__ == "__main__":
    print("🚀 Testing Goalgetter Telegram API")
    print("=" * 50)
    
    try:
        test_telegram_chat()
        test_telegram_user_creation()
        test_conversation_flow()
        test_memory_endpoint()
        
        print("✅ All Telegram API tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

