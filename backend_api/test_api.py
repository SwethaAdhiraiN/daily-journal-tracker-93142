#!/usr/bin/env python3
"""
Basic API test script for Daily Journal API
Tests user registration, login, and journal entry operations
"""
import requests
import sys

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_user_registration():
    """Test user registration"""
    print("\nTesting user registration...")
    user_data = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "TestPass123",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
        print(f"Registration: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"User created: {result['user']['username']}")
            return result.get('access_token')
        else:
            print(f"Registration failed: {response.text}")
            return None
    except Exception as e:
        print(f"Registration error: {e}")
        return None

def test_user_login():
    """Test user login"""
    print("\nTesting user login...")
    login_data = {
        "username": "testuser123",
        "password": "TestPass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"Login: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Login successful: {result['user']['username']}")
            return result.get('access_token')
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_create_entry(token):
    """Test creating a journal entry"""
    print("\nTesting journal entry creation...")
    headers = {"Authorization": f"Bearer {token}"}
    entry_data = {
        "title": "My First Journal Entry",
        "content": "This is a test journal entry created via API test. Today was a good day!",
        "mood": "happy",
        "tags": ["test", "api", "journal"],
        "is_private": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/entries", json=entry_data, headers=headers)
        print(f"Entry creation: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Entry created: {result['title']}")
            return result.get('id')
        else:
            print(f"Entry creation failed: {response.text}")
            return None
    except Exception as e:
        print(f"Entry creation error: {e}")
        return None

def test_get_entries(token):
    """Test getting journal entries"""
    print("\nTesting get journal entries...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/entries", headers=headers)
        print(f"Get entries: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Retrieved {len(result['entries'])} entries")
            return True
        else:
            print(f"Get entries failed: {response.text}")
            return False
    except Exception as e:
        print(f"Get entries error: {e}")
        return False

def test_search_entries(token):
    """Test searching journal entries"""
    print("\nTesting search journal entries...")
    headers = {"Authorization": f"Bearer {token}"}
    params = {"query": "test", "limit": 10}
    
    try:
        response = requests.get(f"{BASE_URL}/api/entries/search/query", params=params, headers=headers)
        print(f"Search entries: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Search found {len(result['entries'])} entries")
            return True
        else:
            print(f"Search failed: {response.text}")
            return False
    except Exception as e:
        print(f"Search error: {e}")
        return False

def main():
    """Run all API tests"""
    print("=== Daily Journal API Test Suite ===")
    
    # Test health check
    if not test_health_check():
        print("❌ Health check failed - server may not be running")
        sys.exit(1)
    
    # Test user registration
    token = test_user_registration()
    if not token:
        # Try login if registration failed (user might already exist)
        token = test_user_login()
        if not token:
            print("❌ Both registration and login failed")
            sys.exit(1)
    
    # Test journal entry operations
    entry_id = test_create_entry(token)
    if not entry_id:
        print("❌ Journal entry creation failed")
        sys.exit(1)
    
    # Test getting entries
    if not test_get_entries(token):
        print("❌ Get entries failed")
        sys.exit(1)
    
    # Test search
    if not test_search_entries(token):
        print("❌ Search entries failed")
        sys.exit(1)
    
    print("\n✅ All API tests passed successfully!")
    print("🎉 Daily Journal API is working correctly!")

if __name__ == "__main__":
    main()
