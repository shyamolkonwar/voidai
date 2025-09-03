
"""
FloatChat Database Manager
==========================

Handles all direct interaction with PostgreSQL database.
Provides connection pooling, SQL validation, and secure query execution.

Author: FloatChat Backend System
"""

import logging
import re
from typing import List, Dict, Any, Optional, Union
import time
from contextlib import contextmanager
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryExecutionResult:
    """Data class for query execution results"""
    success: bool
    data: List[Dict[str, Any]]
    row_count: int
    execution_time: float
    error_message: Optional[str] = None
    column_names: Optional[List[str]] = None

class SQLValidator:
    """
    Security-focused SQL query validator.
    Ensures only safe SELECT statements are executed.
    """

    # Dangerous SQL keywords that should never appear in user queries
    FORBIDDEN_KEYWORDS = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE',
        'REPLACE', 'MERGE', 'CALL', 'EXEC', 'EXECUTE', 'DECLARE', 'SET',
        'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'LOCK'
    ]

    # Dangerous functions and procedures
    FORBIDDEN_FUNCTIONS = [
        'xp_cmdshell', 'sp_configure', 'openrowset', 'opendatasource',
        'pg_read_file', 'pg_ls_dir', 'copy', 'load_file', 'into outfile'
    ]

    @classmethod
    def validate_sql(cls, sql_query: str) -> tuple[bool, str]:
        """
        Validate SQL query for security and correctness.

        Args:
            sql_query: SQL query string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql_query or not sql_query.strip():
            return False, "Empty SQL query"

        # Normalize query for analysis
        normalized_query = sql_query.upper().strip()

        # Remove comments to prevent comment-based attacks
        normalized_query = re.sub(r'--.*', '', normalized_query)
        normalized_query = re.sub(r'/\*.*?\*/', '', normalized_query, flags=re.DOTALL)

        # Must start with SELECT
        if not normalized_query.startswith('SELECT'):
            return False, "Only SELECT statements are allowed"

        # Check for forbidden keywords
        for keyword in cls.FORBIDDEN_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', normalized_query):
                return False, f"Forbidden keyword detected: {keyword}"

        # Check for forbidden functions
        for func in cls.FORBIDDEN_FUNCTIONS:
            if func.upper() in normalized_query:
                return False, f"Forbidden function detected: {func}"

        # Check for potential SQL injection patterns
        injection_patterns = [
            r"';.*--",  # Command termination with comment
            r"\bunion\s+select\b",  # UNION-based injection
            r"\bor\s+1\s*=\s*1\b",  # Classic OR injection
            r"\band\s+1\s*=\s*1\b",  # Classic AND injection
            r"\bor\s+'.*'\s*=\s*'.*'\b",  # String-based OR injection
            r"\\x[0-9a-fA-F]+",  # Hex encoding
            r"char\(",  # Character conversion functions
            r"ascii\(",  # ASCII conversion functions
            r"concat\s*\(",  # String concatenation that might be used maliciously
        ]

        for pattern in injection_patterns:
            if re.search(pattern, normalized_query, re.IGNORECASE):
                return False, f"Potential SQL injection pattern detected"

        # Ensure query doesn't try to access system tables/schemas
        system_patterns = [
            r"\binformation_schema\b",
            r"\bpg_catalog\b",
            r"\bpg_class\b",
            r"\bpg_tables\b",
            r"\bpg_user\b",
            r"\bmysql\b",
            r"\bperformance_schema\b",
            r"\bsys\b"
        ]

        for pattern in system_patterns:
            if re.search(pattern, normalized_query, re.IGNORECASE):
                return False, "Access to system tables/schemas is not allowed"

        # Basic syntax check - ensure balanced parentheses
        if normalized_query.count('(') != normalized_query.count(')'):
            return False, "Unbalanced parentheses in SQL query"

        # Check for multiple statements (semicolon followed by non-whitespace)
        if re.search(r';\s*\S', sql_query):
            return False, "Multiple SQL statements are not allowed"

        return True, "SQL query is valid"

    @classmethod
    def sanitize_sql(cls, sql_query: str) -> str:
        """
        Sanitize SQL query by removing potentially dangerous elements.

        Args:
            sql_query: Raw SQL query

        Returns:
            Sanitized SQL query
        """
        # Remove SQL comments
        sql_query = re.sub(r'--.*', '', sql_query)
        sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)

        # Remove extra whitespace
        sql_query = ' '.join(sql_query.split())

        # Ensure it ends with semicolon
        if not sql_query.endswith(';'):
            sql_query += ';'

        return sql_query

class FloatChatDBManager:
    """
    Database manager for FloatChat PostgreSQL interactions.
    Provides secure, pooled connections and query execution.
    """

    def __init__(self, database_url: str, pool_size: int = 20, max_overflow: int = 0):
        """
        Initialize database manager with connection pooling.

        Args:
            database_url: PostgreSQL connection URL
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
        """
        self.database_url = database_url

        # Create engine with connection pooling
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=3600,   # Recycle connections every hour
            echo=False  # Set to True for SQL logging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # Initialize validator
        self.validator = SQLValidator()

        logger.info("Database manager initialized with connection pooling")

    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.

        Yields:
            SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()

    def test_connection(self) -> bool:
        """
        Test database connectivity.

        Returns:
            Boolean indicating successful connection
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False

    def validate_sql_query(self, sql_query: str) -> tuple[bool, str]:
        """
        Validate SQL query using the security validator.

        Args:
            sql_query: SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.validator.validate_sql(sql_query)

    def execute_query(self, sql_query: str, timeout: int = 30) -> QueryExecutionResult:
        """
        Execute a validated SQL query and return results.

        Args:
            sql_query: SQL SELECT query to execute
            timeout: Query timeout in seconds

        Returns:
            QueryExecutionResult object with query results and metadata
        """
        start_time = time.time()

        try:
            # Step 1: Validate the SQL query
            is_valid, error_message = self.validate_sql_query(sql_query)
            if not is_valid:
                logger.warning(f"SQL validation failed: {error_message}")
                return QueryExecutionResult(
                    success=False,
                    data=[],
                    row_count=0,
                    execution_time=time.time() - start_time,
                    error_message=f"SQL Validation Error: {error_message}"
                )

            # Step 2: Sanitize the query
            sanitized_query = self.validator.sanitize_sql(sql_query)
            logger.info(f"Executing query: {sanitized_query[:200]}...")

            # Step 3: Execute the query
            with self.get_session() as session:
                # Set query timeout
                session.execute(text(f"SET statement_timeout = '{timeout}s'"))

                # Execute the main query
                result = session.execute(text(sanitized_query))
                rows = result.fetchall()

                # Get column names
                column_names = list(result.keys()) if result.keys() else []

                # Convert rows to list of dictionaries
                data = []
                for row in rows:
                    row_dict = {}
                    for i, column_name in enumerate(column_names):
                        # Handle different data types
                        value = row[i]
                        if hasattr(value, 'isoformat'):  # datetime objects
                            value = value.isoformat()
                        elif isinstance(value, (int, float, str, bool)) or value is None:
                            pass  # Keep as-is
                        else:
                            value = str(value)  # Convert other types to string
                        row_dict[column_name] = value
                    data.append(row_dict)

                execution_time = time.time() - start_time

                logger.info(f"Query executed successfully: {len(data)} rows in {execution_time:.2f}s")

                return QueryExecutionResult(
                    success=True,
                    data=data,
                    row_count=len(data),
                    execution_time=execution_time,
                    column_names=column_names
                )

        except SQLAlchemyError as e:
            execution_time = time.time() - start_time
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)

            return QueryExecutionResult(
                success=False,
                data=[],
                row_count=0,
                execution_time=execution_time,
                error_message=error_msg
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)

            return QueryExecutionResult(
                success=False,
                data=[],
                row_count=0,
                execution_time=execution_time,
                error_message=error_msg
            )

    def get_table_info(self, table_names: List[str] = None) -> Dict[str, Any]:
        """
        Get information about database tables and their schemas.

        Args:
            table_names: List of table names to query (if None, gets all tables)

        Returns:
            Dictionary containing table information
        """
        try:
            with self.get_session() as session:
                # Query to get table information
                if table_names:
                    table_filter = "AND table_name IN ({})".format(
                        ','.join([f"'{name}'" for name in table_names])
                    )
                else:
                    table_filter = ""

                query = f"""
                SELECT 
                    table_name,
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' {table_filter}
                ORDER BY table_name, ordinal_position
                """

                result = session.execute(text(query))
                rows = result.fetchall()

                # Organize results by table
                tables_info = {}
                for row in rows:
                    table_name = row[0]
                    if table_name not in tables_info:
                        tables_info[table_name] = {
                            'columns': [],
                            'column_count': 0
                        }

                    tables_info[table_name]['columns'].append({
                        'name': row[1],
                        'type': row[2],
                        'nullable': row[3] == 'YES',
                        'default': row[4]
                    })
                    tables_info[table_name]['column_count'] += 1

                return tables_info

        except Exception as e:
            logger.error(f"Error getting table info: {str(e)}")
            return {}

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get basic database statistics.

        Returns:
            Dictionary containing database statistics
        """
        try:
            with self.get_session() as session:
                stats = {}

                # Get table row counts
                table_stats_query = """
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
                """

                result = session.execute(text(table_stats_query))
                rows = result.fetchall()

                stats['tables'] = []
                for row in rows:
                    stats['tables'].append({
                        'name': row[1],
                        'inserts': row[2],
                        'updates': row[3],
                        'deletes': row[4],
                        'live_rows': row[5],
                        'dead_rows': row[6]
                    })

                # Get database size
                size_query = "SELECT pg_size_pretty(pg_database_size(current_database()))"
                result = session.execute(text(size_query))
                stats['database_size'] = result.scalar()

                return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {}

    def close(self):
        """
        Close database connections and cleanup resources.
        """
        try:
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}")

def main():
    """
    Example usage of the database manager.
    """
    # Configuration
    DATABASE_URL = "postgresql://username:password@localhost:5432/floatchat"

    # Initialize database manager
    db_manager = FloatChatDBManager(DATABASE_URL)

    # Test connection
    if not db_manager.test_connection():
        print("Failed to connect to database")
        return

    # Example queries
    test_queries = [
        "SELECT COUNT(*) as total_floats FROM floats;",
        "SELECT float_id, project_name FROM floats LIMIT 5;",
        "SELECT AVG(temperature) as avg_temp FROM profiles WHERE temperature IS NOT NULL;",
        # This should fail validation:
        "DROP TABLE floats;"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)

        result = db_manager.execute_query(query)

        if result.success:
            print(f"Success! Returned {result.row_count} rows in {result.execution_time:.2f}s")
            if result.data:
                # Print first few rows
                for i, row in enumerate(result.data[:3]):
                    print(f"Row {i+1}: {row}")
                if len(result.data) > 3:
                    print(f"... and {len(result.data) - 3} more rows")
        else:
            print(f"Error: {result.error_message}")

    # Get table information
    print("\n" + "="*60)
    print("TABLE INFORMATION")
    print("="*60)
    table_info = db_manager.get_table_info(['floats', 'cycles', 'profiles'])
    for table_name, info in table_info.items():
        print(f"\nTable: {table_name} ({info['column_count']} columns)")
        for col in info['columns'][:5]:  # Show first 5 columns
            print(f"  - {col['name']}: {col['type']} (nullable: {col['nullable']})")
        if len(info['columns']) > 5:
            print(f"  ... and {len(info['columns']) - 5} more columns")

    # Get database stats
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    stats = db_manager.get_database_stats()
    if stats:
        print(f"Database Size: {stats.get('database_size', 'Unknown')}")
        print("\nTable Statistics:")
        for table in stats.get('tables', []):
            print(f"  {table['name']}: {table['live_rows']} live rows")

    # Cleanup
    db_manager.close()

if __name__ == "__main__":
    main()
