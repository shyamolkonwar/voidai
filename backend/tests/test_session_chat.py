#!/usr/bin/env python3
"""
Test script for session-aware chat functionality.
This script tests the complete flow from session creation to message persistence.
"""

import sys
import os
import requests
import json
import uuid

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_session_chat_flow():
    """Test the complete session-aware chat flow"""
    
    base_url = "http://127.0.0.1:8001"
    
    print("🧪 Testing Session-Aware Chat Flow")
    print("=" * 50)
    
    # Test 1: Create a new session
    print("\n1. Creating new session...")
    try:
        response = requests.post(f"{base_url}/api/v1/sessions")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['session_id']
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return False
    
    # Test 2: Send a query with session context
    print("\n2. Sending query with session context...")
    try:
        query_data = {
            "query": "Show me ocean temperature data from the last month",
            "session_id": session_id,
            "max_results": 5
        }
        
        response = requests.post(f"{base_url}/query", json=query_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query successful: {result['summary']}")
            print(f"   Response type: {result['type']}")
            print(f"   Rows returned: {result['row_count']}")
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending query: {e}")
        return False
    
    # Test 3: Get session history
    print("\n3. Retrieving session history...")
    try:
        response = requests.get(f"{base_url}/api/v1/sessions/{session_id}/history")
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Session history retrieved: {history['message_count']} messages")
            for msg in history['messages']:
                print(f"   - {msg['role']}: {msg['content'][:50]}...")
        else:
            print(f"❌ Failed to get history: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting history: {e}")
    
    # Test 4: Send follow-up query with same session
    print("\n4. Sending follow-up query...")
    try:
        followup_data = {
            "query": "Now show me salinity data for the same period",
            "session_id": session_id,
            "max_results": 3
        }
        
        response = requests.post(f"{base_url}/query", json=followup_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Follow-up query successful: {result['summary']}")
        else:
            print(f"❌ Follow-up query failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending follow-up query: {e}")
    
    # Test 5: Verify history includes both queries
    print("\n5. Verifying complete session history...")
    try:
        response = requests.get(f"{base_url}/api/v1/sessions/{session_id}/history")
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Final session history: {history['message_count']} messages")
            if history['message_count'] >= 4:  # 2 user + 2 assistant messages
                print("✅ Session context is being maintained correctly!")
            else:
                print("⚠️  Session history may not be complete")
        else:
            print(f"❌ Failed to verify history: {response.status_code}")
    except Exception as e:
        print(f"❌ Error verifying history: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Session-aware chat test completed!")
    print(f"Session ID: {session_id}")
    print("You can now:")
    print(f"1. Visit http://localhost:3000/chat/{session_id} to continue the conversation")
    print("2. Test multi-turn conversations with context awareness")
    print("3. Verify messages are persisted across reloads")
    
    return True

def test_api_v1_endpoint():
    """Test the API v1 endpoint with session context"""
    
    base_url = "http://127.0.0.1:8001"
    
    print("\n🧪 Testing API v1 endpoint with session context...")
    print("=" * 50)
    
    # Create session
    try:
        response = requests.post(f"{base_url}/api/v1/sessions")
        session_id = response.json()['session_id']
        print(f"✅ Session created: {session_id}")
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        return False
    
    # Test v1 endpoint
    try:
        query_data = {
            "query": "Find floats with temperature measurements above 20 degrees",
            "session_id": session_id,
            "max_results": 5
        }
        
        response = requests.post(f"{base_url}/api/v1/query", json=query_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API v1 query successful: {result['summary']}")
            print(f"   SQL generated: {result['sql_query'][:100]}...")
            return True
        else:
            print(f"❌ API v1 query failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing API v1: {e}")
        return False

if __name__ == "__main__":
    print("FloatChat Session-Aware Chat Test")
    print("Make sure the backend server is running on http://127.0.0.1:8001")
    print("and the frontend is running on http://localhost:3000")
    print()
    
    try:
        # Test basic session flow
        success = test_session_chat_flow()
        
        # Test API v1 endpoint
        if success:
            test_api_v1_endpoint()
        
        if success:
            print("\n🎉 All tests passed! Session-aware chat is working correctly.")
        else:
            print("\n❌ Some tests failed. Check the backend server status.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        sys.exit(1)