"""
User history tracking for content selections.
Tracks what movies/series users search for and add to their library.
This data can be used in the future to provide personalized recommendations.
"""
from typing import Optional, List
from datetime import datetime, timezone
from models.database import get_db

class UserHistoryManager:
    """
    Manages user interaction history for future recommendation improvements.
    Tracks searches, library additions, and other user actions.
    """

    def __init__(self):
        """Initialize the history manager with database connection."""
        self.db = get_db()

    def log_action(
        self,
        user_id: int,
        content_type: str,
        content_id: str,
        content_name: str,
        action: str
    ) -> None:
        """
        Log a user action for future analysis and recommendations.

        Args:
            user_id: Discord user ID
            content_type: 'movie' or 'series'
            content_id: IMDB or TMDB ID (e.g., 'tt1234567' or 'tmdb:12345')
            content_name: Title of the content
            action: Action type ('search', 'add_to_library', 'view')
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        self.db.execute(
            """
            INSERT INTO user_history (user_id, content_type, content_id, content_name, action, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, content_type, content_id, content_name, action, timestamp)
        )

        print(f"📝 Logged {action} for user {user_id}: {content_name} ({content_id})")

    def log_search(self, user_id: int, content_type: str, content_id: str, content_name: str) -> None:
        """Log when a user searches for content."""
        self.log_action(user_id, content_type, content_id, content_name, "search")

    def log_library_addition(self, user_id: int, content_type: str, content_id: str, content_name: str) -> None:
        """Log when a user adds content to their Stremio library."""
        self.log_action(user_id, content_type, content_id, content_name, "add_to_library")

    def log_view(self, user_id: int, content_type: str, content_id: str, content_name: str) -> None:
        """Log when a user views content details."""
        self.log_action(user_id, content_type, content_id, content_name, "view")

    def get_user_history(self, user_id: int, limit: int = 50) -> List[dict]:
        """
        Get recent history for a user.

        Args:
            user_id: Discord user ID
            limit: Maximum number of records to return

        Returns:
            List of history records as dictionaries
        """
        rows = self.db.fetchall(
            """
            SELECT content_type, content_id, content_name, action, timestamp
            FROM user_history
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (user_id, limit)
        )

        return [
            {
                "content_type": row["content_type"],
                "content_id": row["content_id"],
                "content_name": row["content_name"],
                "action": row["action"],
                "timestamp": row["timestamp"]
            }
            for row in rows
        ]

    def get_user_favorites(self, user_id: int, content_type: Optional[str] = None, limit: int = 10) -> List[dict]:
        """
        Get user's most frequently added content (potential favorites).

        Args:
            user_id: Discord user ID
            content_type: Filter by 'movie' or 'series', or None for all
            limit: Maximum number of results

        Returns:
            List of content with interaction counts
        """
        query = """
            SELECT content_type, content_id, content_name, COUNT(*) as interaction_count
            FROM user_history
            WHERE user_id = ? AND action IN ('add_to_library', 'view')
        """
        params = [user_id]

        if content_type:
            query += " AND content_type = ?"
            params.append(content_type)

        query += """
            GROUP BY content_id
            ORDER BY interaction_count DESC
            LIMIT ?
        """
        params.append(limit)

        rows = self.db.fetchall(query, tuple(params))

        return [
            {
                "content_type": row["content_type"],
                "content_id": row["content_id"],
                "content_name": row["content_name"],
                "interaction_count": row["interaction_count"]
            }
            for row in rows
        ]

    def get_popular_content(self, content_type: Optional[str] = None, days: int = 30, limit: int = 10) -> List[dict]:
        """
        Get most popular content across all users in the last N days.

        Args:
            content_type: Filter by 'movie' or 'series', or None for all
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of popular content with user counts
        """
        query = """
            SELECT content_type, content_id, content_name, COUNT(DISTINCT user_id) as user_count
            FROM user_history
            WHERE action IN ('add_to_library', 'view')
            AND timestamp >= datetime('now', '-' || ? || ' days')
        """
        params = [days]

        if content_type:
            query += " AND content_type = ?"
            params.append(content_type)

        query += """
            GROUP BY content_id
            ORDER BY user_count DESC
            LIMIT ?
        """
        params.append(limit)

        rows = self.db.fetchall(query, tuple(params))

        return [
            {
                "content_type": row["content_type"],
                "content_id": row["content_id"],
                "content_name": row["content_name"],
                "user_count": row["user_count"]
            }
            for row in rows
        ]

    def clear_user_history(self, user_id: int) -> int:
        """
        Clear all history for a user.

        Args:
            user_id: Discord user ID

        Returns:
            Number of records deleted
        """
        cursor = self.db.execute(
            "DELETE FROM user_history WHERE user_id = ?",
            (user_id,)
        )
        count = cursor.rowcount
        print(f"🗑️ Cleared {count} history records for user {user_id}")
        return count
