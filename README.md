# Stremio Discord Bot

A modular Discord bot for managing Stremio libraries with AI-powered recommendations, advanced filtering, and sharing capabilities.

## Features

### 🎬 Content Discovery
- AI-powered movie/TV recommendations using Google Gemini
- Smart search with poster displays
- Language-aware AI responses
- User history tracking for future personalized recommendations

### 📚 Library Management
- View your entire library with rich embeds
- Filter by content type (movies, series, or all)
- Multiple view modes (grid with posters, table list)
- Share library items to channels or via DM
- Track watched/removed items with date filtering

### 🔐 Security
- Per-user authentication via DM (encrypted at rest)
- Fernet encryption for auth keys
- SQLite database for scalable storage (1000+ users)
- Automatic migration from JSON to SQLite
- Docker secrets support for encryption keys
- Read-only secret mounting

### 🌍 Multilingual Support
- Built-in: English, Dutch
- Easily extensible language system
- AI responses in configured language

### 🐳 Infrastructure
- Docker container monitoring
- Automatic service status alerts
- Admin-only detailed diagnostics

### 🖼️ Metadata
- Integrated with AIOmetadata for fast poster fetching
- Enhanced poster quality with RPDB (Rating Poster Database) support
- **Automatic TMDB fallback** when metadata service is unavailable
- Configurable poster database keys (free and premium tiers)
- Smart fallback URLs for maximum coverage
- No external API rate limits
- Supports both IMDb and TMDB IDs

## Quick Start

### 1. Environment Setup
```bash
# Copy example env file
cp .env.example .env

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Edit .env and add your credentials
vi .env
```

### 2. Security Setup (Recommended)
```bash
# Create secrets directory on host
sudo mkdir -p /opt/stremiobot/secrets

# Create encryption key file
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" | sudo tee /opt/stremiobot/secrets/fernet.key

# Secure the key file
sudo chmod 600 /opt/stremiobot/secrets/fernet.key
```

### 3. Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Enable these **Privileged Gateway Intents**:
   - Message Content Intent
   - Server Members Intent (required for DM sharing)
4. Copy the bot token to your `.env` file

### 4. Run the Bot
```bash
docker-compose up -d
```

### 5. Authenticate
Send a DM to the bot:
```
/setauth auth_key: <your_stremio_auth_key>
```

## Slash Commands

This bot uses **Discord's native slash command system** (discord.py 2.6.4):
- All commands start with `/` (no prefix commands)
- Built-in autocomplete and parameter descriptions
- Interactive modals for complex filtering
- Ephemeral responses for privacy
- Type `/` in Discord to see all available commands

**Benefits:**
- Better user experience with Discord's native UI
- Command discovery through autocomplete
- Input validation and parameter types
- Consistent cross-platform behavior

## Commands

**All commands use Discord's slash command system.** Start typing `/` in Discord to see all available commands with autocomplete!

### Search & Discovery
- `/film query: <description>` - Search for movies with AI recommendations
  - Example: `/film query: sci-fi thriller like Inception`
- `/serie query: <description>` - Search for TV shows with AI recommendations
  - Example: `/serie query: mystery series like True Detective`

### Library Management
- `/library` - View all items in grid view (with posters)
- `/library filter: All (List)` - View all items in table format
- `/library filter: Movies Only` - View only movies in table format
- `/library filter: Series Only` - View only series in table format

Each library item can be shared using the action buttons:
- **Share** - Select specific channel or send via DM to users
- **Remove** - Remove item from your Stremio library
- Navigate between items using pagination controls

### Watched Items
- `/watched` - View all watched/removed items (movies and series only)
- `/watched filter_type: Movies Only` - View only watched movies
- `/watched filter_type: Series Only` - View only watched series
- `/watched use_advanced: True` - Opens a modal for advanced filtering:
  - **Content Type**: Filter by movies, series, or all
  - **Removed Status**: Filter by removed (yes/no/all)
  - **Watched Status**: Filter by watched flag (yes/no/all)
  - **Date Range**: Filter by last watched date (YYYY-MM-DD format)
  - Example: Filter removed movies between 2024-01-01 and 2024-12-31

### Authentication (DM Only)
- `/setauth auth_key: <key>` - Set your Stremio auth key
- `/removeauth` - Remove your stored auth key
- `/checkauth` - Verify if auth key is set

### Admin
- `/status` - Check Docker container status
  - Regular users: Simple "All OK" or "Issues detected" message
  - Admin: Detailed status of all monitored containers + DM on failures
- `/ping` - Test bot responsiveness (admin only)
- `/restart container_name: <name>` - Restart a Docker container (admin only)
- `/whoami` - Show your user ID and admin status

### Help
- `/help` - Show available commands with descriptions and examples

## Configuration

### Environment Variables

```env
# Discord Configuration
BOT_TOKEN=your_bot_token_here
CHANNEL_COMMAND_ID=123456789  # Optional: Restrict commands to specific channel
ADMIN_USER_ID=987654321       # Optional: Admin user for detailed status

# API Keys
GEMINI_API_KEY=your_gemini_api_key
TMDB_API_KEY=your_tmdb_key    # Deprecated, kept for backward compatibility

# Metadata Service (Optional - uses TMDB directly if not set)
METADATA_URL=http://metadata:1337  # URL for aiometadata service with RPDB support

# RPDB (Rating Poster Database) Configuration
RPDB_KEY=t0-free-rpdb  # Default: free tier. Premium users can use their own key

# Language Configuration
BOT_LANG=ENGLISH  # Options: ENGLISH, DUTCH

# Docker Container Monitoring
MONITORED_CONTAINERS=container1,container2,container3,...
# Comma-separated list. Leave empty to disable /status command

# Security Configuration
ENCRYPTION_KEY=your_generated_fernet_key  # Or use Docker secrets
```

### Monitored Docker Containers

Configure monitored containers via the `.env` file:

```env
# Comma-separated list of container names to monitor
MONITORED_CONTAINERS=container1,container2,container3,...
```

**Features:**
- The `/status` command checks if all listed containers are running
- If any container is down or missing, admin receives detailed status via DM
- Regular users see a simple "All OK" or "Issues detected" message
- Leave empty or unset to disable the `/status` command entirely

**Note:** Container monitoring is completely optional. If `MONITORED_CONTAINERS` is not configured, the `/status` command will inform users that monitoring is disabled.

### Metadata & Poster Configuration

**Default Behavior:** If `METADATA_URL` is not set, the bot uses **TMDB directly** for posters (requires `TMDB_API_KEY`).

**With Metadata Service:** Set `METADATA_URL` to use aiometadata with RPDB for enhanced poster quality.

```env
# Basic setup (TMDB only)
TMDB_API_KEY=your_tmdb_key

# Enhanced setup (aiometadata + RPDB)
METADATA_URL=http://metadata:1337  # or your metadata service URL
RPDB_KEY=t0-free-rpdb              # optional: enhance poster quality
```

**RPDB Key Types:**
- `t0-free-rpdb` - Free tier (default, works for most use cases)
- Custom premium key - Premium users can use their own RPDB API key for:
  - Higher quality posters
  - More poster variants
  - Better coverage for obscure content

**How it works:**
- **No METADATA_URL**: Uses TMDB directly (simple, works out of the box)
- **With METADATA_URL**: Uses aiometadata with RPDB enhancement
- **Resilient**: Automatically falls back to direct TMDB if metadata service is down
- Language-aware poster selection (defaults to en-US)

### Database Storage

The bot uses **SQLite** for storing user data:

**What's stored:**
- User authentication keys (encrypted with Fernet)
- User interaction history (for future recommendation improvements)

**Location:** `data/stremiobot.db` (auto-created on first run)

**Migration:** If you're upgrading from an older version that used JSON storage, the bot will automatically migrate your data to SQLite on first startup. The old JSON file will be backed up as `user_auth.json.bak`.

**Benefits:**
- Scales to 1000+ users without performance issues
- Better concurrent access handling
- Transaction support for data integrity
- Efficient querying for analytics

## Adding New Languages

### Option 1: Create a New Language File

1. Create `lang/FRENCH.lang`:
```
# French translations
HELP_TITLE=Commandes du Bot
ERROR_COMMAND_NOT_FOUND=Commande inconnue. Utilisez `!help` pour la liste des commandes.
LOADING_LIBRARY=Chargement de la bibliothèque...
# ... (84+ keys total)
```

2. Update `.env`:
```env
BOT_LANG=FRENCH
```

### Option 2: Extend Existing Languages

Simply edit existing `.lang` files in the `lang/` directory. The bot will automatically reload the language on restart.

**Language File Format:**
- Lines starting with `#` are comments
- Format: `KEY=Value`
- Supports multi-line values with proper escaping
- Supports variable substitution with `{variable_name}`

## Project Structure

```
stremiobot/
├── cogs/           # Command modules (search, library, watched, admin, help)
├── lang/           # Translation files (ENGLISH.lang, DUTCH.lang)
├── models/         # Data models (database, user auth, history tracking)
├── services/       # External service integrations (Gemini AI, metadata)
├── utils/          # Utility functions (language loader)
├── views/          # Discord UI components (buttons, selectors, pagination)
├── bot.py          # Main bot entry point
├── config.py       # Configuration management
├── data/           # SQLite database storage (auto-created)
└── docker-compose.yml
```

See individual directory READMEs for detailed documentation.

## Security Best Practices

1. **Never commit `.env` or encryption keys to git**
2. **Use Docker secrets** for production encryption keys
3. **Restrict bot permissions** to only necessary channels
4. **Enable only required Discord intents**
5. **Regularly rotate encryption keys** (requires re-authentication)
6. **Keep the bot updated** for security patches

## Troubleshooting

### Slash commands not appearing
- Wait a few minutes after bot startup for Discord to sync commands
- Try kicking and re-inviting the bot to refresh permissions
- Ensure bot has `applications.commands` scope when invited
- Check bot logs for sync errors: `docker logs stremiobot`

### Bot doesn't respond to commands
- Verify slash commands are synced (check logs for "✅ Synced X slash command(s)")
- Check `CHANNEL_COMMAND_ID` is correct or not set (allows all channels)
- Verify bot has `Send Messages` and `Use Slash Commands` permissions
- Check bot logs: `docker logs stremiobot`

### DM sharing doesn't work
- Enable "Server Members Intent" in Discord Developer Portal
- Restart the bot after enabling the intent

### Encryption key errors
- Ensure encryption key is properly set in `.env` or mounted as Docker secret
- Regenerate key if corrupted: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- Note: Regenerating requires all users to re-authenticate

### Metadata/posters not loading
- Check `METADATA_URL` points to running aiometadata instance
- Verify aiometadata container is accessible from bot container
- Default: `http://metadata:1337` (Docker network)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests if applicable
4. Submit a pull request

## License

MIT License - See LICENSE file for details

