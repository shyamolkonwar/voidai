
"""
FloatChat RAG Core
==================

The AI brain for Text-to-SQL generation using Retrieval Augmented Generation.
Handles query embedding, context retrieval, prompt engineering, and LLM invocation.

Author: FloatChat Backend System
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import json
import time
import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import requests
from dataclasses import dataclass
from geocoding_service import GeographicService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Data class for RAG query results"""
    sql_query: str
    confidence_score: float
    retrieved_context: List[Dict[str, Any]]
    processing_time: float
    reasoning: str

class FloatChatRAGCore:
    """
    Core RAG system for converting natural language queries to SQL.
    Implements embedding-based retrieval and prompt engineering for LLM interaction.
    """

    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8000, 
                 llm_endpoint: str = "http://localhost:11434/api/generate"):
        """
        Initialize the RAG core system.

        Args:
            chroma_host: ChromaDB server host
            chroma_port: ChromaDB server port
            llm_endpoint: LLM API endpoint (Ollama format)
        """
        self.llm_endpoint = llm_endpoint

        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Loaded sentence transformer model")

        # Initialize ChromaDB client
        self.chroma_client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )

        # Get ChromaDB collection
        try:
            self.collection = self.chroma_client.get_collection(name="float_profiles")
            logger.info("Connected to ChromaDB collection: float_profiles")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB collection: {str(e)}")
            raise

        # Database schema for MCP context
        self.database_schema = """
        -- FloatChat Database Schema --

        Table: floats
        Columns:
        - float_id (VARCHAR, PRIMARY KEY): Unique identifier for the float
        - wmo_id (VARCHAR): World Meteorological Organization ID
        - project_name (VARCHAR): Project name (e.g., ARGO, SOLO)
        - pi_name (VARCHAR): Principal Investigator name
        - platform_type (VARCHAR): Type of float platform
        - deployment_date (TIMESTAMP): Date when float was deployed
        - last_update (TIMESTAMP): Last data update timestamp

        Table: cycles
        Columns:
        - cycle_id (VARCHAR, PRIMARY KEY): Unique identifier for the cycle
        - float_id (VARCHAR, FOREIGN KEY): References floats.float_id
        - cycle_number (INTEGER): Cycle number for this float
        - profile_date (TIMESTAMP): Date of the profile measurement
        - latitude (FLOAT): Latitude of measurement location
        - longitude (FLOAT): Longitude of measurement location
        - profile_type (VARCHAR): Type of profile (A=ascending, D=descending)

        Table: profiles
        Columns:
        - profile_id (VARCHAR, PRIMARY KEY): Unique identifier for the profile point
        - cycle_id (VARCHAR, FOREIGN KEY): References cycles.cycle_id
        - pressure (FLOAT): Pressure measurement in dbar
        - temperature (FLOAT): Temperature measurement in Celsius
        - salinity (FLOAT): Salinity measurement in PSU
        - depth (FLOAT): Depth in meters
        - quality_flag (INTEGER): Quality control flag (1=good, 2=probably good, etc.)
        """

        # Few-shot examples for Text-to-SQL
        self.few_shot_examples = [
            {
                "query": "Show me all temperature measurements from float 5904471",
                "sql": "SELECT p.temperature, p.depth, c.profile_date, c.latitude, c.longitude FROM profiles p JOIN cycles c ON p.cycle_id = c.cycle_id JOIN floats f ON c.float_id = f.float_id WHERE f.float_id = '5904471' AND p.temperature IS NOT NULL ORDER BY c.profile_date, p.depth;"
            },
            {
                "query": "Find the deepest measurement for each float in the Pacific Ocean",
                "sql": "SELECT f.float_id, f.platform_type, MAX(p.depth) as max_depth, COUNT(p.profile_id) as total_measurements FROM floats f JOIN cycles c ON f.float_id = c.float_id JOIN profiles p ON c.cycle_id = p.cycle_id WHERE c.longitude BETWEEN -180 AND -60 AND c.latitude BETWEEN -60 AND 60 GROUP BY f.float_id, f.platform_type ORDER BY max_depth DESC;"
            },
            {
                "query": "What is the average salinity at 1000 meter depth across all floats?",
                "sql": "SELECT AVG(p.salinity) as avg_salinity, COUNT(*) as measurement_count FROM profiles p WHERE p.depth BETWEEN 950 AND 1050 AND p.salinity IS NOT NULL AND p.quality_flag IN (1, 2);"
            },
            {
                "query": "Show me temperature measurements near Mumbai",
                "sql": "SELECT p.temperature, p.depth, c.profile_date, c.latitude, c.longitude, (6371 * acos(cos(radians(19.0760)) * cos(radians(c.latitude)) * cos(radians(c.longitude) - radians(72.8777)) + sin(radians(19.0760)) * sin(radians(c.latitude)))) as distance_km FROM profiles p JOIN cycles c ON p.cycle_id = c.cycle_id WHERE (6371 * acos(cos(radians(19.0760)) * cos(radians(c.latitude)) * cos(radians(c.longitude) - radians(72.8777)) + sin(radians(19.0760)) * sin(radians(c.latitude)))) <= 500 AND p.temperature IS NOT NULL AND p.quality_flag IN (1, 2) ORDER BY distance_km, c.profile_date;"
            }
        ]

        # Initialize geographic service
        self.geo_service = GeographicService(use_external_geocoding=True)
        logger.info("Initialized geographic service")

        # Safety constraints
        self.safety_constraints = """
        CRITICAL SAFETY CONSTRAINTS:
        1. ONLY generate SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, CREATE, or ALTER statements.
        2. Always include appropriate WHERE clauses to limit result size.
        3. Use proper JOINs to connect related tables.
        4. Include quality control filters (quality_flag IN (1, 2)) for measurement data.
        5. Handle NULL values appropriately with IS NOT NULL or COALESCE.
        6. Use LIMIT clause for queries that might return large datasets.
        7. Always use parameterized queries to prevent SQL injection (though this will be handled by the database layer).
        8. When location context is provided, use geographic proximity queries with proper coordinate filtering.
        """

    def embed_query(self, query: str) -> List[float]:
        """
        Convert user's natural language query to vector embedding.

        Args:
            query: Natural language query string

        Returns:
            Query embedding as a list of floats
        """
        try:
            embedding = self.embedding_model.encode(query)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding query: {str(e)}")
            raise

    def retrieve_context(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context documents from ChromaDB.

        Args:
            query_embedding: Query vector embedding
            top_k: Number of top results to retrieve

        Returns:
            List of relevant context documents with metadata
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )

            context_documents = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    doc = {
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                    }
                    context_documents.append(doc)

            logger.info(f"Retrieved {len(context_documents)} context documents")
            return context_documents

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []

    def engineer_prompt(self, user_query: str, context_docs: List[Dict[str, Any]], conversation_context: Optional[str] = None) -> str:
        """
        Assemble the complete prompt for the LLM with all required components.

        Args:
            user_query: Original user query
            context_docs: Retrieved context documents
            conversation_context: Optional conversation history for context awareness

        Returns:
            Complete engineered prompt string
        """
        # Format context documents
        context_text = ""
        if context_docs:
            context_text = "\n\nRELEVANT CONTEXT FROM DATABASE:\n"
            for i, doc in enumerate(context_docs, 1):
                context_text += f"\nContext {i} (Similarity: {doc['similarity_score']:.3f}):\n"
                context_text += doc['content']
                context_text += f"\nMetadata: {json.dumps(doc['metadata'], indent=2)}\n"
                context_text += "-" * 80 + "\n"

        # Format conversation context if available
        conversation_text = ""
        if conversation_context:
            conversation_text = f"\n\nCONVERSATION HISTORY:\n{conversation_context}\n"

        # Check for location context
        location_context = None
        enhanced_query, location_context = self.geo_service.enhance_query_with_location(user_query)
        
        location_text = ""
        fallback_guidance = ""
        if location_context:
            location_text = f"\n\nGEOGRAPHIC CONTEXT:\n{location_context}\n"
            fallback_guidance = """

IF NO RESULTS FOUND:
- Try removing geographic constraints to check if data exists
- Consider using broader geographic boundaries
- Check if location is outside ARGO deployment areas
- Try querying for global data with ORDER BY distance from target location"""

        # Format few-shot examples
        examples_text = "\n\nFEW-SHOT EXAMPLES:\n"
        for i, example in enumerate(self.few_shot_examples, 1):
            examples_text += f"\nExample {i}:\n"
            examples_text += f"Human: {example['query']}\n"
            examples_text += f"SQL: {example['sql']}\n"
            examples_text += "-" * 40 + "\n"

        # Assemble complete prompt
        prompt = f"""You are a specialized SQL generator for oceanographic ARGO float data. Your task is to convert natural language queries into precise SQL SELECT statements.

{conversation_text}

{self.safety_constraints}

DATABASE SCHEMA:
{self.database_schema}

{context_text}

{location_text}

{examples_text}

USER QUERY: {user_query}

Based on the provided context, database schema, conversation history, and examples, generate a SQL SELECT statement that accurately answers the user's query.

IMPORTANT GUIDELINES:
- Only generate a single SQL SELECT statement
- Use proper table aliases for readability
- Include appropriate JOINs to connect related tables
- Add quality control filters for measurement data
- Use LIMIT if the query might return many rows
- Handle NULL values appropriately
- If the user query mentions location, map, or coordinates, you MUST include the `c.latitude` and `c.longitude` columns from the `cycles` table in the SELECT statement.
- When geographic context is provided, use the Haversine formula for proximity searches with the cycles table (aliased as 'c')
- Return only the SQL statement, no explanations
- PAY SPECIAL ATTENTION TO THE CONVERSATION HISTORY ABOVE - use it to understand the context of follow-up questions
- If the user asks a follow-up question without specifying details, infer the context from the previous conversation
{fallback_guidance}

SQL:"""

        return prompt

    def invoke_llm(self, prompt: str, model: str = "deepseek-chat") -> str:
        """Send prompt to DeepSeek LLM and return the generated SQL.

        Args:
            prompt: Complete engineered prompt
            model: DeepSeek model name (default: deepseek-chat)

        Returns:
            Generated SQL query string
        """
        try:
            # Get API key from environment
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise Exception("DEEPSEEK_API_KEY environment variable not set")

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a specialized SQL generator for oceanographic ARGO float data. Your task is to convert natural language queries into precise SQL SELECT statements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,  # Low temperature for consistent SQL generation
                "max_tokens": 512,
                "top_p": 0.9
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            response = requests.post(
                self.llm_endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                sql_query = result['choices'][0]['message']['content'].strip()

                # Clean up the SQL query
                sql_query = self._clean_sql_output(sql_query)

                logger.info(f"DeepSeek LLM generated SQL query: {sql_query[:100]}...")
                return sql_query
            else:
                logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                raise Exception(f"DeepSeek API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Error invoking DeepSeek LLM: {str(e)}")
            raise

    def _clean_sql_output(self, sql_output: str) -> str:
        """
        Clean and validate the SQL output from the LLM.

        Args:
            sql_output: Raw SQL output from LLM

        Returns:
            Cleaned SQL query
        """
        # Remove markdown code blocks if present
        sql_output = sql_output.replace('```sql', '').replace('```', '')

        # Remove extra whitespace and newlines
        sql_output = ' '.join(sql_output.split())

        # Ensure it ends with semicolon
        if not sql_output.endswith(';'):
            sql_output += ';'

        return sql_output

    def calculate_confidence_score(self, context_docs: List[Dict[str, Any]], 
                                 sql_query: str) -> float:
        """
        Calculate a confidence score for the generated SQL query.

        Args:
            context_docs: Retrieved context documents
            sql_query: Generated SQL query

        Returns:
            Confidence score between 0 and 1
        """
        score = 0.0

        # Base score from context relevance
        if context_docs:
            avg_similarity = sum(doc['similarity_score'] for doc in context_docs) / len(context_docs)
            score += avg_similarity * 0.6

        # Score based on SQL query characteristics
        if sql_query:
            # Check for proper SELECT statement
            if sql_query.upper().strip().startswith('SELECT'):
                score += 0.2

            # Check for proper JOIN usage
            if 'JOIN' in sql_query.upper():
                score += 0.1

            # Check for WHERE clause
            if 'WHERE' in sql_query.upper():
                score += 0.1

        return min(score, 1.0)

    def process_query(self, user_query: str, conversation_context: Optional[str] = None) -> QueryResult:
        """
        Complete RAG pipeline: embed query, retrieve context, generate SQL.

        Args:
            user_query: Natural language query from user
            conversation_context: Optional conversation history for context awareness

        Returns:
            QueryResult object with SQL query and metadata
        """
        start_time = time.time()

        try:
            # Step 1: Embed the query
            logger.info(f"Processing query: {user_query}")
            query_embedding = self.embed_query(user_query)

            # Step 2: Retrieve relevant context
            context_docs = self.retrieve_context(query_embedding)

            # Step 3: Engineer the prompt with conversation context
            prompt = self.engineer_prompt(user_query, context_docs, conversation_context)

            # Step 4: Invoke LLM
            sql_query = self.invoke_llm(prompt)

            # Step 5: Calculate confidence score
            confidence_score = self.calculate_confidence_score(context_docs, sql_query)

            processing_time = time.time() - start_time

            result = QueryResult(
                sql_query=sql_query,
                confidence_score=confidence_score,
                retrieved_context=context_docs,
                processing_time=processing_time,
                reasoning="Here is the data you requested:"
            )

            logger.info(f"Query processed successfully in {processing_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

def main():
    """
    Example usage of the RAG core system.
    """
    # Initialize RAG core
    rag_core = FloatChatRAGCore()

    # Example queries
    test_queries = [
        "Show me temperature data from float 5904471",
        "What's the average salinity in the Pacific Ocean?",
        "Find the deepest measurements from all floats"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)

        try:
            result = rag_core.process_query(query)
            print(f"Generated SQL: {result.sql_query}")
            print(f"Confidence Score: {result.confidence_score:.3f}")
            print(f"Processing Time: {result.processing_time:.2f}s")
            print(f"Context Documents: {len(result.retrieved_context)}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
