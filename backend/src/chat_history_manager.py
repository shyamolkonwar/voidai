"""
Chat History Manager
===================
"""

import logging
import uuid
import tiktoken
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text, exc
from sqlalchemy.orm import Session

from src.db_manager import FloatChatDBManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """
    Manages chat history operations including storage, retrieval, and session management.
    """

    def __init__(self, db_manager: FloatChatDBManager):
        """
        Initialize chat history manager with database connection.

        Args:
            db_manager: Instance of FloatChatDBManager
        """
        self.db_manager = db_manager
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Configuration for token management
        self.max_tokens_per_message = 1000  # Maximum tokens per message to store
        self.max_session_tokens = 4000      # Maximum tokens per session before summarization
        self.max_messages_per_session = 20  # Maximum messages per session

    def create_session(self) -> str:
        """
        Create a new chat session and return the session ID.

        Returns:
            New session UUID as string
        """
        return str(uuid.uuid4())

    def add_message(self, session_id: str, role: str, message: str, metadata: Optional[Dict] = None, full_response: Optional[Dict] = None) -> bool:
        """
        Add a message to the chat history for a specific session.

        Args:
            session_id: UUID of the chat session
            role: 'user' or 'assistant'
            message: The message content
            metadata: Optional metadata dictionary
            full_response: Optional complete AI response data including tables, maps, etc.

        Returns:
            Boolean indicating success
        """
        try:
            # Count tokens for this message
            token_count = self.count_tokens(message)
            
            # Truncate message if it exceeds maximum token limit
            if token_count > self.max_tokens_per_message:
                logger.warning(f"Message exceeds token limit ({token_count} > {self.max_tokens_per_message}), truncating")
                # Simple truncation - in production, you might want smarter truncation
                message = message[:self.max_tokens_per_message * 4] + "... [truncated]"
            
            with self.db_manager.get_session() as session:
                # Include token count in metadata
                message_metadata = metadata or {}
                message_metadata['token_count'] = token_count
                message_metadata['timestamp'] = datetime.now().isoformat()
                
                # Get the next turn index for this session
                next_turn_index = self.get_next_turn_index(session_id)
                
                query = text("""
                    INSERT INTO chat_history (session_id, turn_index, role, message, metadata, full_response, created_at)
                    VALUES (:session_id, :turn_index, :role, :message, CAST(:metadata AS jsonb), CAST(:full_response AS jsonb), :created_at)
                """)
                
                params = {
                    'session_id': session_id,
                    'turn_index': next_turn_index,
                    'role': role,
                    'message': message,
                    'metadata': json.dumps(message_metadata),  # Convert dict to JSON string
                    'full_response': json.dumps(full_response) if full_response else '{}',  # Convert full response to JSON string
                    'created_at': datetime.now()
                }
                
                session.execute(query, params)
                session.commit()
                logger.info(f"Added {role} message to session {session_id} ({token_count} tokens)")
                print(f"DEBUG: Successfully saved {role} message to session {session_id}")
                
                # Check if we need to optimize the conversation history
                self.optimize_conversation_history(session_id)
                
                return True
                
        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to add message to chat history: {str(e)}")
            return False

    def get_recent_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent chat history for a session.

        Args:
            session_id: UUID of the chat session
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries with role, content, and timestamp
        """
        try:
            with self.db_manager.get_session() as session:
                query = text("""
                    SELECT role, message, full_response, created_at
                    FROM chat_history
                    WHERE session_id = :session_id
                    ORDER BY turn_index DESC
                    LIMIT :limit
                """)
                
                result = session.execute(query, {'session_id': session_id, 'limit': limit})
                messages = []
                
                for row in result:
                    messages.append({
                        'role': row[0],
                        'content': row[1],
                        'full_response': row[2] if row[2] else {},
                        'timestamp': row[3].isoformat() if row[3] else None
                    })
                
                # Reverse to get chronological order
                messages.reverse()
                return messages
                
        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to retrieve chat history: {str(e)}")
            return []

    def get_conversation_context(self, session_id: str, max_turns: int = 8) -> str:
        """
        Format conversation history as a context string for LLM prompts.

        Args:
            session_id: UUID of the chat session
            max_turns: Maximum number of conversation turns to include

        Returns:
            Formatted conversation context string
        """
        messages = self.get_recent_history(session_id, max_turns * 2)  # *2 because each turn has user+assistant
        
        if not messages:
            return ""
        
        context_lines = []
        for msg in messages:
            if msg['role'] == 'user':
                context_lines.append(f"User: {msg['content']}")
            elif msg['role'] == 'assistant':
                context_lines.append(f"Assistant: {msg['content']}")
        
        return "\n".join(context_lines)

    def get_message_count(self, session_id: str) -> int:
        """
        Get the number of messages in a session.

        Args:
            session_id: UUID of the chat session

        Returns:
            Number of messages in the session
        """
        try:
            with self.db_manager.get_session() as session:
                query = text("""
                    SELECT COUNT(*) 
                    FROM chat_history 
                    WHERE session_id = :session_id
                """)
                
                result = session.execute(query, {'session_id': session_id})
                return result.scalar() or 0
                
        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to get message count: {str(e)}")
            return 0

    def get_next_turn_index(self, session_id: str) -> int:
        """
        Get the next turn index for a session.
        
        Args:
            session_id: UUID of the chat session
            
        Returns:
            Next turn index (1 for new session, max + 1 for existing session)
        """
        try:
            with self.db_manager.get_session() as session:
                query = text("""
                    SELECT MAX(turn_index)
                    FROM chat_history
                    WHERE session_id = :session_id
                """)
                
                result = session.execute(query, {'session_id': session_id})
                max_turn_index = result.scalar()
                
                return (max_turn_index or 0) + 1
                
        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to get next turn index: {str(e)}")
            return 1  # Fallback to first turn

    def cleanup_old_messages(self, session_id: str, max_messages: int = 20) -> bool:
        """
        Clean up old messages to keep conversation history manageable.

        Args:
            session_id: UUID of the chat session
            max_messages: Maximum number of messages to keep

        Returns:
            Boolean indicating success
        """
        try:
            with self.db_manager.get_session() as session:
                # Get current message count
                count = self.get_message_count(session_id)
                
                if count <= max_messages:
                    return True
                
                # Delete oldest messages beyond the limit
                query = text("""
                    DELETE FROM chat_history
                    WHERE session_id = :session_id
                    AND turn_index IN (
                        SELECT turn_index
                        FROM chat_history
                        WHERE session_id = :session_id
                        ORDER BY turn_index
                        LIMIT :delete_count
                    )
                """)
                
                delete_count = count - max_messages
                session.execute(query, {
                    'session_id': session_id,
                    'delete_count': delete_count
                })
                session.commit()
                
                logger.info(f"Cleaned up {delete_count} old messages from session {session_id}")
                return True
                
        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to cleanup old messages: {str(e)}")
            return False

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists in the database.

        Args:
            session_id: UUID to check

        Returns:
            Boolean indicating if session exists
        """
        try:
            with self.db_manager.get_session() as session:
                query = text("""
                    SELECT EXISTS(
                        SELECT 1 
                        FROM chat_history 
                        WHERE session_id = :session_id
                        LIMIT 1
                    )
                """)
                
                result = session.execute(query, {'session_id': session_id})
                return result.scalar() or False
                
        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to check session existence: {str(e)}")
            return False

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string using tiktoken.
        
        Args:
            text: Input text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Failed to count tokens: {str(e)}")
            # Fallback: approximate token count (4 characters per token)
            return len(text) // 4

    def get_session_token_count(self, session_id: str) -> int:
        """
        Get total token count for a session.
        
        Args:
            session_id: UUID of the chat session
            
        Returns:
            Total number of tokens in the session
        """
        try:
            with self.db_manager.get_session() as session:
                query = text("""
                    SELECT message FROM chat_history
                    WHERE session_id = :session_id
                """)
                
                result = session.execute(query, {'session_id': session_id})
                messages = [row[0] for row in result]
                
                total_tokens = 0
                for message in messages:
                    total_tokens += self.count_tokens(message)
                
                return total_tokens
                
        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to get session token count: {str(e)}")
            return 0

    def optimize_conversation_history(self, session_id: str) -> bool:
        """
        Optimize conversation history by summarizing old messages when token limit is exceeded.
        
        Args:
            session_id: UUID of the chat session
            
        Returns:
            Boolean indicating if optimization was performed
        """
        try:
            total_tokens = self.get_session_token_count(session_id)
            
            if total_tokens <= self.max_session_tokens:
                return False
                
            logger.info(f"Session {session_id} exceeds token limit ({total_tokens} > {self.max_session_tokens}), optimizing...")
            
            # Get oldest messages to summarize
            with self.db_manager.get_session() as session:
                query = text("""
                    SELECT turn_index, role, message
                    FROM chat_history
                    WHERE session_id = :session_id
                    ORDER BY turn_index
                    LIMIT 5
                """)
                
                result = session.execute(query, {'session_id': session_id})
                old_messages = [{"turn_index": row[0], "role": row[1], "message": row[2]} for row in result]
                
                if not old_messages:
                    return False
                
                # Create a summary of old messages (in a real implementation, this would use an LLM)
                summary_text = "Previous conversation summary: "
                for msg in old_messages:
                    summary_text += f"{msg['role']}: {msg['message'][:100]}... "
                
                # Add summary as a system message
                self.add_message(session_id, "system", summary_text)
                
                # Delete the old summarized messages
                delete_query = text("""
                    DELETE FROM chat_history
                    WHERE session_id = :session_id
                    AND turn_index IN :turn_indices
                """)
                
                turn_indices = tuple(msg["turn_index"] for msg in old_messages)
                session.execute(delete_query, {
                    'session_id': session_id,
                    'turn_indices': turn_indices
                })
                session.commit()
                
                logger.info(f"Optimized session {session_id}: summarized {len(old_messages)} messages")
                return True
                
        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to optimize conversation history: {str(e)}")
            return False

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all chat sessions with their metadata.

        Returns:
            List of session dictionaries with id, message_count, and last_activity
        """
        try:
            with self.db_manager.get_session() as session:
                query = text("""
                    SELECT
                        session_id,
                        COUNT(*) as message_count,
                        MAX(created_at) as last_activity
                    FROM chat_history
                    GROUP BY session_id
                    ORDER BY last_activity DESC
                """)
                
                result = session.execute(query)
                sessions = []
                
                for row in result:
                    sessions.append({
                        'id': row[0],
                        'message_count': row[1],
                        'last_activity': row[2].isoformat() if row[2] else None,
                        'title': self._generate_session_title(row[0])  # Generate a title based on first message
                    })
                
                return sessions
        except Exception as e:
            logger.error(f"Failed to get all sessions: {str(e)}")
            return []

    def _generate_session_title(self, session_id: str) -> str:
        """
        Generate a title for a session based on its first user message.
        
        Args:
            session_id: UUID of the chat session
            
        Returns:
            Title for the session
        """
        try:
            with self.db_manager.get_session() as session:
                query = text("""
                    SELECT message
                    FROM chat_history
                    WHERE session_id = :session_id AND role = 'user'
                    ORDER BY turn_index ASC
                    LIMIT 1
                """)
                
                result = session.execute(query, {'session_id': session_id})
                first_message = result.scalar()
                
                if first_message:
                    # Use first few words of the first user message as title
                    words = first_message.split()[:5]
                    return ' '.join(words) + ('...' if len(words) == 5 else '')
                else:
                    return "New Chat"
        except Exception as e:
            logger.error(f"Failed to generate session title: {str(e)}")
            return "New Chat"

# Example usage
def main():
    """Example usage of ChatHistoryManager"""
    from src.db_manager import FloatChatDBManager
    
    # Initialize database manager
    db_url = "postgresql://username:password@localhost:5432/floatchat"
    db_manager = FloatChatDBManager(db_url)
    chat_manager = ChatHistoryManager(db_manager)
    
    # Create a new session
    session_id = chat_manager.create_session()
    print(f"Created new session: {session_id}")
    
    # Add some messages
    chat_manager.add_message(session_id, "user", "Hello, how are you?")
    chat_manager.add_message(session_id, "assistant", "I'm doing well, thank you!")
    chat_manager.add_message(session_id, "user", "Can you help me with ocean data?")
    
    # Get conversation context
    context = chat_manager.get_conversation_context(session_id)
    print("Conversation context:")
    print(context)
    
    # Get message count
    count = chat_manager.get_message_count(session_id)
    print(f"Total messages: {count}")

if __name__ == "__main__":
    main()