import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_signup_errors():
    print("Testing signup errors...")
    
    # Test 1: Try to signup with existing email
    print("\n1. Testing duplicate email...")
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
            "full_name": "Test User"
        })
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_login_errors():
    print("\nTesting login errors...")
    
    # Test 1: Try to login with wrong password
    print("\n1. Testing wrong password...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_signup_errors()
    test_login_errors() 