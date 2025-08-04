#!/usr/bin/env python3
"""
Test script for interview evaluation functionality
"""

import requests
import json

# Test data
test_interview_data = {
    "session_id": "test_session_123",
    "conversation": [
        {
            "role": "assistant",
            "content": "What does tokenization entail, and why is it critical for LLMs?",
            "timestamp": "2025-07-30T15:00:00Z"
        },
        {
            "role": "user",
            "content": "Tokenization is the process of breaking down text into smaller units called tokens. These tokens can be words, subwords, or characters. It's critical for LLMs because it allows the model to process and understand text in a structured way.",
            "timestamp": "2025-07-30T15:00:30Z"
        },
        {
            "role": "assistant",
            "content": "Thank you for that detailed explanation. What distinguishes LoRA from QLoRA in fine-tuning LLMs?",
            "timestamp": "2025-07-30T15:01:00Z"
        },
        {
            "role": "user",
            "content": "LoRA (Low-Rank Adaptation) is a parameter-efficient fine-tuning method that adds small rank decomposition matrices to existing weights. QLoRA (Quantized LoRA) extends this by using quantized weights to reduce memory usage while maintaining performance.",
            "timestamp": "2025-07-30T15:01:30Z"
        },
        {
            "role": "assistant",
            "content": "Great, thanks for sharing your perspective. How do you prevent overfitting in large language models?",
            "timestamp": "2025-07-30T15:02:00Z"
        },
        {
            "role": "user",
            "content": "To prevent overfitting in large language models, you can use techniques like dropout, early stopping, regularization, data augmentation, and cross-validation. It's also important to monitor validation metrics and use sufficient training data.",
            "timestamp": "2025-07-30T15:02:30Z"
        }
    ],
    "questions": [
        "What does tokenization entail, and why is it critical for LLMs?",
        "What distinguishes LoRA from QLoRA in fine-tuning LLMs?",
        "How do you prevent overfitting in large language models?"
    ],
    "answers": [
        "Tokenization is the process of breaking down text into smaller units called tokens. These tokens can be words, subwords, or characters. It's critical for LLMs because it allows the model to process and understand text in a structured way.",
        "LoRA (Low-Rank Adaptation) is a parameter-efficient fine-tuning method that adds small rank decomposition matrices to existing weights. QLoRA (Quantized LoRA) extends this by using quantized weights to reduce memory usage while maintaining performance.",
        "To prevent overfitting in large language models, you can use techniques like dropout, early stopping, regularization, data augmentation, and cross-validation. It's also important to monitor validation metrics and use sufficient training data."
    ]
}

def test_interview_evaluation():
    """Test the interview evaluation API"""
    
    print("🧪 Testing Interview Evaluation API")
    print("=" * 50)
    
    # Test 1: Evaluate interview
    print("\n1. Testing interview evaluation...")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/interview/evaluate",
            json=test_interview_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Interview evaluation successful!")
            print(f"   Session ID: {result['session_id']}")
            print(f"   Total Score: {result['total_score']}/{result['max_score']}")
            print(f"   Percentage: {result['percentage']:.1f}%")
            print(f"   Questions Evaluated: {result['questions_evaluated']}")
            print(f"   Overall Analysis: {result['overall_analysis'][:100]}...")
            
            # Print detailed feedback
            print("\n   Detailed Feedback:")
            for i, feedback in enumerate(result['detailed_feedback'], 1):
                print(f"   Q{i}: Score {feedback['score']}/100 - {feedback['feedback'][:80]}...")
                
        else:
            print(f"❌ Interview evaluation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing interview evaluation: {e}")
        return False
    
    # Test 2: Get interview history
    print("\n2. Testing interview history...")
    try:
        response = requests.get("http://localhost:8000/api/v1/interview/history")
        
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Interview history retrieved successfully!")
            print(f"   Found {len(history)} interview sessions")
            
            if history:
                latest = history[0]
                print(f"   Latest session: {latest['session_id']}")
                print(f"   Score: {latest['total_score']}/{latest['max_score']} ({latest['percentage']:.1f}%)")
                
        else:
            print(f"❌ Interview history failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing interview history: {e}")
        return False
    
    # Test 3: Get specific session result
    print("\n3. Testing specific session result...")
    try:
        response = requests.get(f"http://localhost:8000/api/v1/interview/{test_interview_data['session_id']}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Session result retrieved successfully!")
            print(f"   Session ID: {result['session_id']}")
            print(f"   Score: {result['total_score']}/{result['max_score']}")
            
        else:
            print(f"❌ Session result failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing session result: {e}")
        return False
    
    print("\n🎉 All tests passed! Interview evaluation system is working correctly.")
    return True

def test_database_schema():
    """Test database schema"""
    print("\n🔍 Testing Database Schema")
    print("=" * 50)
    
    import sqlite3
    
    try:
        conn = sqlite3.connect("voice-assistant/backend/interview_assistant.db")
        cursor = conn.cursor()
        
        # Check qa_pairs table schema
        cursor.execute("PRAGMA table_info(qa_pairs)")
        columns = cursor.fetchall()
        
        print("📋 qa_pairs table schema:")
        for col in columns:
            print(f"   {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
        
        # Check if score column exists
        score_column = any(col[1] == 'score' for col in columns)
        if score_column:
            print("✅ Score column exists in qa_pairs table")
        else:
            print("❌ Score column missing from qa_pairs table")
            return False
        
        # Check recent data
        cursor.execute("SELECT COUNT(*) FROM qa_pairs")
        count = cursor.fetchone()[0]
        print(f"📊 Total Q&A pairs in database: {count}")
        
        if count > 0:
            cursor.execute("SELECT question, answer, score FROM qa_pairs ORDER BY timestamp DESC LIMIT 3")
            recent = cursor.fetchall()
            print("📝 Recent Q&A pairs:")
            for i, (q, a, s) in enumerate(recent, 1):
                print(f"   {i}. Q: {q[:50]}...")
                print(f"      A: {a[:50]}...")
                print(f"      Score: {s}")
                print()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error testing database schema: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Interview Evaluation System Tests")
    print("=" * 60)
    
    # Test database schema first
    if not test_database_schema():
        print("❌ Database schema test failed. Please fix database issues first.")
        exit(1)
    
    # Test interview evaluation
    if test_interview_evaluation():
        print("\n✅ All tests passed! The interview evaluation system is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        exit(1) 