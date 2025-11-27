"""
Configuration management for the Stremio Discord bot.
This module loads and validates all environment variables needed by the bot.
"""
import os
from typing import Optional

class Config:
    """
    Central configuration class that loads settings from environment variables.
    Using a class allows us to validate configuration at startup and provides
    a single source of truth for all settings.
    """

    # Discord Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    COMMAND_CHANNEL_ID: Optional[int] = None
    ADMIN_USER_ID: Optional[int] = None

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")  # Used for direct TMDB posters (default if no metadata service)
    METADATA_URL: str = os.getenv("METADATA_URL", "")  # Optional: aiometadata service URL (uses TMDB directly if not set)
    RPDB_KEY: str = os.getenv("RPDB_KEY", "t0-free-rpdb")  # RPDB poster database key

    # Language Configuration
    BOT_LANG: str = os.getenv("BOT_LANG", "ENGLISH")

    # Security Configuration
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")

    # Docker Configuration
    # Load from env or use defaults
    MONITORED_CONTAINERS: list[str] = []
    
    @classmethod
    def load(cls) -> None:
        """
        Load and validate configuration from environment variables.
        This method converts string environment variables to appropriate types
        and validates that required settings are present.
        """
        # Parse integer IDs, allowing None if not set
        channel_id = os.getenv("CHANNEL_COMMAND_ID")
        if channel_id:
            cls.COMMAND_CHANNEL_ID = int(channel_id)

        admin_id = os.getenv("ADMIN_USER_ID")
        if admin_id:
            cls.ADMIN_USER_ID = int(admin_id)

        # Parse monitored containers from comma-separated list
        # If not set, leave empty (disables /status command)
        containers_env = os.getenv("MONITORED_CONTAINERS", "")
        if containers_env:
            cls.MONITORED_CONTAINERS = [c.strip() for c in containers_env.split(",") if c.strip()]
        else:
            cls.MONITORED_CONTAINERS = []

        # Validate required settings
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN must be set in environment variables")

        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
    
    @classmethod
    def print_debug_info(cls) -> None:
        """Print configuration information for debugging purposes."""
        print("=== DEBUG INFO ===")
        print(f"BOT_TOKEN exists: {bool(cls.BOT_TOKEN)}")
        print(f"COMMAND_CHANNEL_ID: {cls.COMMAND_CHANNEL_ID}")
        print(f"ADMIN_USER_ID: {cls.ADMIN_USER_ID}")
        print(f"GEMINI_API_KEY exists: {bool(cls.GEMINI_API_KEY)}")
        print(f"TMDB_API_KEY exists: {bool(cls.TMDB_API_KEY)}")
        print(f"BOT_LANG: {cls.BOT_LANG}")
        if cls.MONITORED_CONTAINERS:
            print(f"MONITORED_CONTAINERS: {len(cls.MONITORED_CONTAINERS)} containers")
            for container in cls.MONITORED_CONTAINERS:
                print(f"  - {container}")
        else:
            print("MONITORED_CONTAINERS: not configured (/status disabled)")
        print("==================")
