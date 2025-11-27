"""
Database management for SQLite storage.
Handles schema creation, migrations, and connection management.
"""
import sqlite3
import os
from pathlib import Path
from typing import Optional

class Database:
    """SQLite database manager for user data."""

    def __init__(self, db_path: str = "data/stremiobot.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        # Ensure data directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._init_schema()

    def _connect(self):
        """Establish database connection with proper settings."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Access columns by name

        # Enable WAL mode for better concurrent access
        self.conn.execute("PRAGMA journal_mode=WAL")

        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys=ON")

    def _init_schema(self):
        """Create database schema if it doesn't exist."""
        cursor = self.conn.cursor()

        # User authentication table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_auth (
                user_id INTEGER PRIMARY KEY,
                encrypted_auth_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User selection history table (for future recommendation improvements)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content_type TEXT NOT NULL,  -- 'movie' or 'series'
                content_id TEXT NOT NULL,    -- IMDB or TMDB ID
                content_name TEXT,           -- Title of the movie/series
                action TEXT NOT NULL,        -- 'search', 'add_to_library', 'view'
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_auth(user_id) ON DELETE CASCADE
            )
        """)

        # Index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_history_user_id
            ON user_history(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_history_timestamp
            ON user_history(timestamp DESC)
        """)

        self.conn.commit()
        print("✅ Database schema initialized")

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection.

        Returns:
            SQLite connection object
        """
        return self.conn

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute(self, query: str, params: tuple = ()):
        """Execute a query and return cursor.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Cursor object
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute query and fetch one result.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Single row or None
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute query and fetch all results.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of rows
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


# Global database instance
_db_instance: Optional[Database] = None

def get_db() -> Database:
    """Get or create global database instance.

    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
