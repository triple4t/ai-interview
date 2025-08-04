#!/usr/bin/env python3
"""
Test to demonstrate that the system always processes the latest responses
"""

import requests
import json
import time

def test_latest_responses():
    """Test that the system processes the latest responses, not old ones"""
    
    print("🧪 Testing Latest Responses Processing")
    print("=" * 50)
    
    # Test 1: Send a response with "I don't know"
    print("📝 Test 1: Sending 'I don't know' responses...")
    
    test_data_1 = {
        "session_id": f"latest_test_1_{int(time.time())}",
        "conversation": [
            {
                "role": "assistant",
                "content": "What does tokenization entail, and why is it critical for LLMs?",
                "timestamp": "2025-07-30T15:00:00Z"
            },
            {
                "role": "user", 
                "content": "I don't know",
                "timestamp": "2025-07-30T15:00:30Z"
            },
            {
                "role": "assistant",
                "content": "What is the role of positional encoding in transformers?",
                "timestamp": "2025-07-30T15:01:00Z"
            },
            {
                "role": "user",
                "content": "I don't know",
                "timestamp": "2025-07-30T15:01:30Z"
            },
            {
                "role": "assistant", 
                "content": "How do you prevent overfitting in large language models?",
                "timestamp": "2025-07-30T15:02:00Z"
            },
            {
                "role": "user",
                "content": "I don't know",
                "timestamp": "2025-07-30T15:02:30Z"
            }
        ],
        "questions": [
            "What does tokenization entail, and why is it critical for LLMs?",
            "What is the role of positional encoding in transformers?",
            "How do you prevent overfitting in large language models?"
        ],
        "answers": [
            "I don't know",
            "I don't know", 
            "I don't know"
        ]
    }
    
    response_1 = requests.post(
        "http://localhost:8000/api/v1/interview/evaluate",
        json=test_data_1,
        headers={"Content-Type": "application/json"}
    )
    
    if response_1.status_code == 200:
        result_1 = response_1.json()
        print(f"✅ Test 1 Result: {result_1['total_score']}/{result_1['max_score']} ({result_1['percentage']:.1f}%)")
        print(f"   Session ID: {result_1['session_id']}")
    else:
        print(f"❌ Test 1 failed: {response_1.status_code}")
    
    time.sleep(2)  # Wait a moment
    
    # Test 2: Send a response with good answers
    print("\n📝 Test 2: Sending good answers...")
    
    test_data_2 = {
        "session_id": f"latest_test_2_{int(time.time())}",
        "conversation": [
            {
                "role": "assistant",
                "content": "What does tokenization entail, and why is it critical for LLMs?",
                "timestamp": "2025-07-30T15:00:00Z"
            },
            {
                "role": "user", 
                "content": "Tokenization is breaking text into tokens for LLM processing",
                "timestamp": "2025-07-30T15:00:30Z"
            },
            {
                "role": "assistant",
                "content": "What is the role of positional encoding in transformers?",
                "timestamp": "2025-07-30T15:01:00Z"
            },
            {
                "role": "user",
                "content": "Positional encoding adds position information to tokens",
                "timestamp": "2025-07-30T15:01:30Z"
            },
            {
                "role": "assistant", 
                "content": "How do you prevent overfitting in large language models?",
                "timestamp": "2025-07-30T15:02:00Z"
            },
            {
                "role": "user",
                "content": "Use regularization, dropout, and early stopping",
                "timestamp": "2025-07-30T15:02:30Z"
            }
        ],
        "questions": [
            "What does tokenization entail, and why is it critical for LLMs?",
            "What is the role of positional encoding in transformers?",
            "How do you prevent overfitting in large language models?"
        ],
        "answers": [
            "Tokenization is breaking text into tokens for LLM processing",
            "Positional encoding adds position information to tokens",
            "Use regularization, dropout, and early stopping"
        ]
    }
    
    response_2 = requests.post(
        "http://localhost:8000/api/v1/interview/evaluate",
        json=test_data_2,
        headers={"Content-Type": "application/json"}
    )
    
    if response_2.status_code == 200:
        result_2 = response_2.json()
        print(f"✅ Test 2 Result: {result_2['total_score']}/{result_2['max_score']} ({result_2['percentage']:.1f}%)")
        print(f"   Session ID: {result_2['session_id']}")
    else:
        print(f"❌ Test 2 failed: {response_2.status_code}")
    
    # Check the latest result in the database
    print("\n🔍 Checking latest result in database...")
    history_response = requests.get("http://localhost:8000/api/v1/interview/history")
    if history_response.status_code == 200:
        history = history_response.json()
        if len(history) > 0:
            latest = history[0]
            print(f"✅ Latest result in database:")
            print(f"   Session ID: {latest['session_id']}")
            print(f"   Score: {latest['total_score']}/{latest['max_score']}")
            print(f"   Percentage: {latest['percentage']:.1f}%")
            print(f"   Created: {latest['created_at']}")
            
            # Verify it matches the latest test
            if latest['session_id'] == result_2['session_id']:
                print("✅ SUCCESS: Database contains the latest response!")
            else:
                print("❌ ERROR: Database contains old response!")
        else:
            print("⚠️ No results found in database")
    else:
        print(f"❌ Failed to fetch history: {history_response.status_code}")

if __name__ == "__main__":
    print("🚀 Testing Latest Responses Processing")
    print("=" * 60)
    
    test_latest_responses()
    
    print("\n✅ Test completed!") 