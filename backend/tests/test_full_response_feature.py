#!/usr/bin/env python3
"""
Test script to verify that the full response feature is working correctly.
This script tests that complete AI responses including tables, maps, and visualizations
are properly saved and retrieved from the database.
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from src.chat_history_manager import ChatHistoryManager
from src.db_manager import FloatChatDBManager

def test_full_response_feature():
    """Test the full response feature"""
    
    # Initialize database manager
    db_url = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    db_manager = FloatChatDBManager(db_url)
    chat_manager = ChatHistoryManager(db_manager)
    
    # Test database connection
    if not db_manager.test_connection():
        print("❌ Database connection failed")
        return False
    
    print("✅ Database connection successful")
    
    # Create a test session
    session_id = chat_manager.create_session()
    print(f"✅ Created test session: {session_id}")
    
    # Test data for full response (simulating a map response)
    test_full_response = {
        "type": "map",
        "data": [
            {"latitude": 14.87, "longitude": 65.774, "temperature": 26.49, "depth": 10.0},
            {"latitude": 14.87, "longitude": 65.774, "temperature": 26.49, "depth": 20.0},
            {"latitude": 14.87, "longitude": 65.774, "temperature": 26.50, "depth": 30.0}
        ],
        "sql_query": "SELECT latitude, longitude, temperature, depth FROM profiles LIMIT 3",
        "row_count": 3,
        "confidence_score": 0.85,
        "execution_time": 1.23,
        "reasoning": "Generated SQL query to show temperature data points",
        "summary": "Showing 3 geographic data points",
        "success": True
    }
    
    # Add a user message
    user_success = chat_manager.add_message(session_id, "user", "Show me temperature data on a map")
    print(f"✅ User message added: {user_success}")
    
    # Add an assistant message with full response data
    assistant_success = chat_manager.add_message(
        session_id, 
        "assistant", 
        "Showing 3 geographic data points",
        full_response=test_full_response
    )
    print(f"✅ Assistant message with full response added: {assistant_success}")
    
    # Retrieve the chat history
    messages = chat_manager.get_recent_history(session_id, limit=10)
    print(f"✅ Retrieved {len(messages)} messages from history")
    
    # Check if the full response data is preserved
    assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
    
    if assistant_messages:
        assistant_msg = assistant_messages[0]
        if 'full_response' in assistant_msg:
            full_response = assistant_msg['full_response']
            print("✅ Full response data found in retrieved message")
            
            # Verify the response data
            if (full_response.get('type') == 'map' and 
                len(full_response.get('data', [])) == 3 and
                full_response.get('row_count') == 3):
                print("✅ Full response data is complete and correct")
                print(f"   - Type: {full_response.get('type')}")
                print(f"   - Data points: {len(full_response.get('data', []))}")
                print(f"   - Row count: {full_response.get('row_count')}")
                print(f"   - Summary: {full_response.get('summary')}")
                return True
            else:
                print("❌ Full response data is incomplete or incorrect")
                print(f"   Full response: {json.dumps(full_response, indent=2)}")
                return False
        else:
            print("❌ No full response data found in retrieved message")
            print(f"   Message content: {assistant_msg}")
            return False
    else:
        print("❌ No assistant messages found in history")
        return False

if __name__ == "__main__":
    print("🧪 Testing full response feature...")
    
    try:
        success = test_full_response_feature()
        if success:
            print("\n🎉 Full response feature test PASSED!")
            print("The system is correctly saving and retrieving complete AI responses.")
        else:
            print("\n💥 Full response feature test FAILED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)