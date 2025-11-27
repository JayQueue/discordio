"""
Data models and storage.

Models represent data structures and handle persistence. This keeps
database/storage logic separate from business logic.
"""

from .user_auth import UserAuthManager

__all__ = ['UserAuthManager']
