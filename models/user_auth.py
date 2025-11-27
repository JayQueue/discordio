"""
User authentication storage for Stremio credentials.
Each Discord user can set their own Stremio auth key via DM.
Auth keys are encrypted at rest using Fernet encryption.

Storage backend: SQLite for better scalability and concurrent access.
"""
import json
import os
import base64
from typing import Optional
from datetime import datetime, timezone
from cryptography.fernet import Fernet
from config import Config
from models.database import get_db

class UserAuthManager:
    """
    Manages Stremio authentication keys for Discord users.
    This class provides persistence of auth keys across bot restarts
    with encryption at rest for security.

    Storage: SQLite database (migrated from JSON for better scalability)
    """

    def __init__(self):
        """
        Initialize the auth manager with SQLite storage.
        Automatically migrates from old JSON storage if it exists.
        """
        self.cipher = self._get_cipher()
        self.db = get_db()

        # Migrate from old JSON storage if it exists
        self._migrate_from_json()

    def _get_cipher(self) -> Fernet:
        """
        Get or create the encryption cipher using the key from mounted secret file.
        The encryption key should be mounted at /run/secrets/fernet.key
        Falls back to ENCRYPTION_KEY env var for backwards compatibility.
        If neither exists, generates a temporary key (not recommended for production).
        """
        encryption_key = None

        # Try to read from Docker secret file first (preferred method)
        secret_path = "/run/secrets/fernet.key"
        if os.path.exists(secret_path):
            try:
                with open(secret_path, 'r') as f:
                    encryption_key = f.read().strip()
                print(f"✅ Loaded encryption key from {secret_path}")
            except Exception as e:
                print(f"⚠️ Could not read encryption key from {secret_path}: {e}")

        # Fall back to environment variable
        if not encryption_key:
            encryption_key = Config.ENCRYPTION_KEY
            if encryption_key:
                print("✅ Loaded encryption key from environment variable")

        # Last resort: generate temporary key (insecure!)
        if not encryption_key:
            print("⚠️ WARNING: No encryption key found!")
            print("⚠️ Please mount key at /run/secrets/fernet.key")
            print("⚠️ Or set ENCRYPTION_KEY in .env")
            print("⚠️ Generating temporary key (will be lost on restart!)")
            encryption_key = Fernet.generate_key().decode()

        # Ensure the key is in bytes
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()

        return Fernet(encryption_key)

    def _encrypt(self, data: str) -> str:
        """Encrypt a string and return base64 encoded result."""
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded data and return the original string."""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            print(f"⚠️ Failed to decrypt data: {e}")
            return None

    def _migrate_from_json(self) -> None:
        """
        Migrate auth data from old JSON storage to SQLite.
        This runs automatically on first startup after upgrade.
        """
        json_file = "data/user_auth.json"
        if not os.path.exists(json_file):
            return

        print("🔄 Migrating auth data from JSON to SQLite...")

        try:
            with open(json_file, 'r') as f:
                encrypted_data = json.load(f)

            migrated_count = 0
            for user_id_str, data in encrypted_data.items():
                # Decrypt the auth key
                decrypted_key = self._decrypt(data["auth_key"])
                if not decrypted_key:
                    print(f"⚠️ Could not decrypt auth key for user {user_id_str}, skipping")
                    continue

                # Re-encrypt and store in SQLite
                user_id = int(user_id_str)
                encrypted_key = self._encrypt(decrypted_key)

                # Insert into database (use INSERT OR REPLACE to handle duplicates)
                self.db.execute(
                    """
                    INSERT OR REPLACE INTO user_auth (user_id, encrypted_auth_key, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, encrypted_key, data.get("set_at"), datetime.now(timezone.utc).isoformat())
                )
                migrated_count += 1

            print(f"✅ Migrated {migrated_count} auth keys from JSON to SQLite")

            # Rename old JSON file to .bak
            backup_file = json_file + ".bak"
            os.rename(json_file, backup_file)
            print(f"📦 Backed up old JSON file to {backup_file}")

        except Exception as e:
            print(f"❌ Migration failed: {e}")

    def set_auth_key(self, user_id: int, auth_key: str) -> None:
        """
        Store an encrypted Stremio auth key for a specific user.

        Args:
            user_id: Discord user ID
            auth_key: Stremio authentication key (stored encrypted)
        """
        encrypted_key = self._encrypt(auth_key)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Use INSERT OR REPLACE to handle both new and existing users
        self.db.execute(
            """
            INSERT OR REPLACE INTO user_auth (user_id, encrypted_auth_key, created_at, updated_at)
            VALUES (
                ?,
                ?,
                COALESCE((SELECT created_at FROM user_auth WHERE user_id = ?), ?),
                ?
            )
            """,
            (user_id, encrypted_key, user_id, timestamp, timestamp)
        )

        print(f"🔑 Set encrypted auth key for user {user_id}")

    def get_auth_key(self, user_id: int) -> Optional[str]:
        """
        Retrieve and decrypt a user's Stremio auth key.

        Args:
            user_id: Discord user ID

        Returns:
            The decrypted auth key if set, None otherwise
        """
        row = self.db.fetchone(
            "SELECT encrypted_auth_key FROM user_auth WHERE user_id = ?",
            (user_id,)
        )

        if row:
            return self._decrypt(row["encrypted_auth_key"])

        return None

    def remove_auth_key(self, user_id: int) -> bool:
        """
        Remove a user's Stremio auth key.

        Args:
            user_id: Discord user ID

        Returns:
            True if a key was removed, False if user had no key
        """
        cursor = self.db.execute(
            "DELETE FROM user_auth WHERE user_id = ?",
            (user_id,)
        )

        if cursor.rowcount > 0:
            print(f"🗑️ Removed auth key for user {user_id}")
            return True

        return False

    def has_auth_key(self, user_id: int) -> bool:
        """Check if a user has set their auth key."""
        row = self.db.fetchone(
            "SELECT 1 FROM user_auth WHERE user_id = ?",
            (user_id,)
        )
        return row is not None

    def get_user_count(self) -> int:
        """Get the total number of users with auth keys stored.

        Returns:
            Number of users with auth keys
        """
        row = self.db.fetchone("SELECT COUNT(*) as count FROM user_auth")
        return row["count"] if row else 0
