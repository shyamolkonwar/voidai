#!/usr/bin/env python3
"""
Test script to verify conversational query handling with DeepSeek LLM
"""

import requests
import json
import os

def test_conversational_query():
    """Test conversational query handling"""
    
    base_url = "http://127.0.0.1:8001"
    
    print("🧪 Testing Conversational Query with DeepSeek LLM")
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
    
    # Test 2: Send conversational queries
    conversational_queries = [
        "hello",
        "thanks",
        "how are you",
        "what can you help me with"
    ]
    
    for query in conversational_queries:
        print(f"\n📝 Testing: '{query}'")
        try:
            query_data = {
                "query": query,
                "session_id": session_id,
                "max_results": 5
            }
            
            response = requests.post(f"{base_url}/api/v1/query", json=query_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Response type: {result['response_type']}")
                
                # Handle both conversational and help response formats
                if isinstance(result['data'], list) and len(result['data']) > 0:
                    first_item = result['data'][0]
                    if isinstance(first_item, dict) and 'message' in first_item:
                        message = first_item['message']
                        print(f"✅ Message: {message[:100]}...")
                    else:
                        message = str(first_item)
                        print(f"✅ Response: {message[:100]}...")
                else:
                    message = str(result['data'])
                    print(f"✅ Response: {message[:100]}...")
                
                if result['response_type'] in ['conversational', 'help']:
                    print(f"🎯 {result['response_type'].title()} handling working correctly!")
                else:
                    print(f"⚠️  Unexpected response type: '{result['response_type']}'")
            else:
                print(f"❌ Query failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing query '{query}': {e}")
    
    print("\n✅ Conversational query test completed!")
    return True

if __name__ == "__main__":
    # Check if DeepSeek API key is available
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("⚠️  DEEPSEEK_API_KEY not set - will use fallback responses")
    else:
        print("✅ DEEPSEEK_API_KEY found")
    
    test_conversational_query()