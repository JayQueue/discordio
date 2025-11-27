# Models Directory

Data models and persistence layer for the Discord bot.

## Overview

This directory contains data models that handle user authentication and data storage. Models abstract database operations and provide a clean interface for cogs to interact with persistent data.

## Available Models

### 🔐 user_auth.py

**Purpose:** Secure storage and retrieval of Stremio authentication keys

**Class:** `UserAuthManager`

#### Features

- **Encrypted Storage** - Uses Fernet symmetric encryption (AES-128-CBC)
- **Per-User Keys** - Stores auth keys mapped to Discord user IDs
- **Docker Secrets Support** - Reads encryption key from mounted secret file
- **Fallback Encryption** - Environment variable fallback for backward compatibility
- **JSON Persistence** - Stores encrypted data in `data/user_auth.json`
- **Automatic Initialization** - Creates data directory and file if missing

#### Encryption Flow

```
User Auth Key (plaintext)
    ↓
Base64 Encode
    ↓
Fernet Encrypt with ENCRYPTION_KEY
    ↓
Store in JSON file
    ↓
Decrypt on retrieval
    ↓
Base64 Decode
    ↓
Return plaintext to application
```

#### Security Features

1. **Key Storage Priority**
   - First: `/run/secrets/fernet.key` (Docker secret, read-only)
   - Second: `ENCRYPTION_KEY` environment variable
   - Last: Generate temporary key (not recommended, warns user)

2. **File Permissions**
   - Encryption key file should be `chmod 600` (owner read/write only)
   - JSON data file created with default Docker container permissions

3. **Encryption Algorithm**
   - Fernet (symmetric encryption)
   - Based on AES-128-CBC
   - HMAC authentication for integrity
   - Automatic key rotation support (requires re-authentication)

## Usage Examples

### Basic Usage

```python
from models.user_auth import UserAuthManager

# Initialize manager
auth_manager = UserAuthManager()

# Store a user's auth key
user_id = 123456789
auth_key = "user_stremio_auth_key_here"
auth_manager.set_auth_key(user_id, auth_key)

# Retrieve auth key
retrieved_key = auth_manager.get_auth_key(user_id)
# Returns: "user_stremio_auth_key_here" or None if not found

# Check if user has auth key
has_auth = auth_manager.has_auth_key(user_id)
# Returns: True or False

# Remove auth key
auth_manager.remove_auth_key(user_id)
```

### In a Cog

```python
from discord.ext import commands
from models.user_auth import UserAuthManager

class MyCog(commands.Cog):
    def __init__(self, bot, auth_manager: UserAuthManager):
        self.bot = bot
        self.auth_manager = auth_manager

    @commands.command(name="mycommand")
    async def my_command(self, ctx):
        user_id = ctx.author.id
        auth_key = self.auth_manager.get_auth_key(user_id)

        if not auth_key:
            await ctx.send("Please authenticate first with !setauth")
            return

        # Use auth_key for API calls
        # ...
```

### Cog Registration

```python
# In bot.py setup_hook():
from cogs import my_cog

await my_cog.setup(self, self.auth_manager)
```

## API Reference

### UserAuthManager

#### Methods

##### `__init__(self, data_file: str = "data/user_auth.json")`
Initialize the auth manager.

**Parameters:**
- `data_file` - Path to JSON storage file (default: `data/user_auth.json`)

**Behavior:**
- Creates `data/` directory if missing
- Creates JSON file if missing
- Loads existing auth keys into memory
- Initializes Fernet cipher

---

##### `set_auth_key(self, user_id: int, auth_key: str) -> None`
Store an encrypted auth key for a user.

**Parameters:**
- `user_id` - Discord user ID (integer)
- `auth_key` - Stremio authentication key (string)

**Behavior:**
- Encrypts the auth key using Fernet
- Stores in memory dictionary
- Persists to JSON file
- Overwrites existing key if present

---

##### `get_auth_key(self, user_id: int) -> Optional[str]`
Retrieve and decrypt a user's auth key.

**Parameters:**
- `user_id` - Discord user ID (integer)

**Returns:**
- Decrypted auth key (string) if found
- `None` if user has no stored key

---

##### `has_auth_key(self, user_id: int) -> bool`
Check if a user has a stored auth key.

**Parameters:**
- `user_id` - Discord user ID (integer)

**Returns:**
- `True` if user has auth key
- `False` otherwise

---

##### `remove_auth_key(self, user_id: int) -> bool`
Remove a user's auth key.

**Parameters:**
- `user_id` - Discord user ID (integer)

**Returns:**
- `True` if key was removed
- `False` if user had no key

**Behavior:**
- Removes from memory dictionary
- Persists changes to JSON file

---

##### `_get_cipher(self) -> Fernet`
Internal method to get or create the Fernet cipher.

**Returns:**
- Configured Fernet cipher instance

**Key Loading Priority:**
1. Read from `/run/secrets/fernet.key` (Docker secret)
2. Read from `ENCRYPTION_KEY` environment variable
3. Generate temporary key (prints warnings)

## Data Storage

### File Structure

**Location:** `data/user_auth.json`

**Format:**
```json
{
  "123456789": "gAAAAABl...",
  "987654321": "gAAAAABm..."
}
```

- **Keys:** Discord user IDs (as strings)
- **Values:** Encrypted auth keys (Fernet tokens)

### Encryption Key Storage

#### Option 1: Docker Secrets (Recommended)

Create encryption key file on host:
```bash
sudo mkdir -p /opt/stremiobot/secrets
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" | sudo tee /opt/stremiobot/secrets/fernet.key
sudo chmod 600 /opt/stremiobot/secrets/fernet.key
```

Mount in `docker-compose.yml`:
```yaml
volumes:
  - /opt/stremiobot/secrets/fernet.key:/run/secrets/fernet.key:ro
```

#### Option 2: Environment Variable

Set in `.env`:
```env
ENCRYPTION_KEY=your_fernet_key_here
```

Generate key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Security Considerations

### Best Practices

1. **Never commit encryption keys** to version control
2. **Use Docker secrets** in production (read-only, outside container)
3. **Rotate keys periodically** (requires user re-authentication)
4. **Limit file permissions** on encryption key file (`chmod 600`)
5. **Backup encrypted data** before key rotation
6. **Monitor for failed decryptions** (indicates corrupted data or wrong key)

### Attack Vectors

| Threat | Mitigation |
|--------|-----------|
| Key exposure in env vars | Use Docker secrets mounted read-only |
| JSON file access | Docker container isolation + file permissions |
| Memory dumps | Encryption at rest (not in memory) |
| Key rotation downtime | Plan maintenance window for re-auth |
| Brute force | Fernet uses strong encryption (AES-128) |

### Encryption Key Rotation

When rotating encryption keys:

1. **Backup current data:**
   ```bash
   docker cp stremiobot:/app/data/user_auth.json ./backup_auth.json
   ```

2. **Generate new key:**
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. **Update encryption key** (Docker secret or .env)

4. **Clear auth data** (cannot decrypt with new key):
   ```bash
   docker exec stremiobot rm /app/data/user_auth.json
   docker-compose restart
   ```

5. **Notify users** to re-authenticate with `!setauth`

## Error Handling

### Common Errors

#### `cryptography.fernet.InvalidToken`
**Cause:** Encryption key changed or data corrupted
**Fix:** Clear `data/user_auth.json` and have users re-authenticate

#### `FileNotFoundError: /run/secrets/fernet.key`
**Cause:** Docker secret not mounted
**Fix:** Check docker-compose.yml volume mount or use environment variable

#### `No ENCRYPTION_KEY found` warnings
**Cause:** No encryption key configured
**Fix:** Set ENCRYPTION_KEY or mount Docker secret

## Testing

### Unit Testing

```python
import unittest
from models.user_auth import UserAuthManager

class TestUserAuth(unittest.TestCase):
    def setUp(self):
        self.manager = UserAuthManager("test_auth.json")

    def test_set_and_get(self):
        self.manager.set_auth_key(12345, "test_key")
        retrieved = self.manager.get_auth_key(12345)
        self.assertEqual(retrieved, "test_key")

    def test_remove(self):
        self.manager.set_auth_key(12345, "test_key")
        self.manager.remove_auth_key(12345)
        self.assertIsNone(self.manager.get_auth_key(12345))
```

### Integration Testing

1. Set auth key via DM: `!setauth test_key_123`
2. Verify persistence: Restart bot, check key still works
3. Remove key: `!removeauth`
4. Verify removal: Try using library commands

## Future Enhancements

Potential improvements:

- [ ] Database backend (PostgreSQL/SQLite) for scalability
- [ ] Multi-key support per user (multiple Stremio accounts)
- [ ] Automatic key expiration/refresh
- [ ] Audit logging for auth changes
- [ ] Key derivation from master password
- [ ] Support for asymmetric encryption
- [ ] Redis cache for frequently accessed keys
- [ ] Bulk export/import for migrations

## Dependencies

- `cryptography` - Fernet encryption library
- `json` - JSON serialization
- `os` - File system operations
- `config.py` - Configuration management

Install dependencies:
```bash
pip install cryptography
```

Or via requirements.txt:
```bash
pip install -r requirements.txt
```
