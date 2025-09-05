#!/usr/bin/env python3
"""
Test script to verify context awareness in FloatChat backend.
This script tests if the system properly uses conversation context from previous messages.
"""

import requests
import json
import time

# Backend API URL
BACKEND_URL = "http://localhost:8001"

def test_context_awareness():
    """Test that the backend properly uses conversation context"""
    
    print("Testing FloatChat Context Awareness")
    print("=" * 40)
    
    # Create a new session
    session_response = requests.post(f"{BACKEND_URL}/api/v1/sessions")
    if session_response.status_code != 200:
        print("❌ Failed to create session")
        return False
    
    session_data = session_response.json()
    session_id = session_data["session_id"]
    print(f"✅ Created session: {session_id}")
    
    # First query: ask about apex data
    first_query = {
        "query": "show me 5 temperature data of apex",
        "session_id": session_id,
        "include_context": True,
        "max_results": 5
    }
    
    print(f"\n1. First query: {first_query['query']}")
    first_response = requests.post(f"{BACKEND_URL}/api/v1/query", json=first_query)
    
    if first_response.status_code != 200:
        print("❌ First query failed")
        return False
    
    first_data = first_response.json()
    print(f"✅ First response: {first_data['reasoning'][:100]}...")
    print(f"   SQL: {first_data['sql_query']}")
    
    # Wait a moment for processing
    time.sleep(1)
    
    # Second query: ask for latest data (should use context from first query)
    second_query = {
        "query": "show me latest",
        "session_id": session_id,
        "include_context": True,
        "max_results": 5
    }
    
    print(f"\n2. Second query: {second_query['query']}")
    second_response = requests.post(f"{BACKEND_URL}/api/v1/query", json=second_query)
    
    if second_response.status_code != 200:
        print("❌ Second query failed")
        return False
    
    second_data = second_response.json()
    print(f"✅ Second response: {second_data['reasoning'][:100]}...")
    print(f"   SQL: {second_data['sql_query']}")
    
    # Check if the second query shows context awareness
    # It should mention "apex" or use similar context from first query
    if "apex" in second_data['sql_query'].lower() or "apex" in second_data['reasoning'].lower():
        print("\n🎉 SUCCESS: Context awareness is working!")
        print("   The second query correctly used context from the first query about 'apex'")
        return True
    else:
        print("\n❌ FAILED: Context awareness is not working")
        print("   The second query didn't seem to use context from the first query")
        print("   Expected to see 'apex' in the SQL or reasoning")
        return False

if __name__ == "__main__":
    try:
        success = test_context_awareness()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        exit(1)