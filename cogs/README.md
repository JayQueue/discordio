# Cogs Directory

Discord bot command modules (cogs) that organize functionality into separate, reloadable components.

## Overview

Cogs are modular command groups that can be loaded, unloaded, and reloaded independently. Each cog handles a specific domain of functionality.

**Framework:** discord.py 2.6.4 with native slash command support (`app_commands`)

## Available Cogs

### 🔍 search.py
**Purpose:** Content search and AI recommendations

**Slash Commands:**
- `/film query: <description>` - Search for movies with AI
- `/serie query: <description>` - Search for TV shows with AI

**Features:**
- Integration with Google Gemini AI for smart recommendations
- Language-aware responses (respects `BOT_LANG` setting)
- Interactive selection with buttons
- Automatic addition to Stremio library
- Poster display for each result
- Parameter descriptions with autocomplete

**Key Components:**
- `SearchCog` - Main command handler
- `GeminiService` integration for AI recommendations
- `TMDBService` integration for poster fetching

**Dependencies:**
- `services/gemini.py`
- `services/tmdb.py`
- `views/search_views.py`
- `models/user_auth.py`

---

### 📚 library.py
**Purpose:** Personal library management and viewing

**Slash Commands:**
- `/library` - View all items (grid view)
- `/library filter: All (List)` - View all items (table view)
- `/library filter: Movies Only` - View movies only (table view)
- `/library filter: Series Only` - View series only (table view)
- `/setauth auth_key: <key>` - Set Stremio auth key (DM only)
- `/removeauth` - Remove auth key (DM only)
- `/checkauth` - Check if auth key is set (DM only)

**Features:**
- Multiple view modes (grid with posters, table list)
- Content filtering with Choice-based dropdown selector
- Individual item sharing to channels or DMs
- Pagination for large libraries
- Ephemeral messages (private to user)
- Share buttons for each item in table view
- Enhanced posters with RPDB support

**View Modes:**
1. **Grid View** - One item per page with large poster
2. **Table View** - 5 items per page with compact info

**Key Components:**
- `LibraryCog` - Main command handler
- `LibraryPaginationView` - Pagination controls
- `ShareItemView` - Sharing interface with channel/user selectors

**Dependencies:**
- `views/library_views.py`
- `services/tmdb.py`
- `models/user_auth.py`

---

### 👁️ watched.py
**Purpose:** Track and filter watched/removed items

**Slash Commands:**
- `/watched` - View all watched/removed items (movies and series only)
- `/watched filter_type: Movies Only` - View movies only
- `/watched filter_type: Series Only` - View series only
- `/watched use_advanced: True` - Open interactive modal for advanced filtering

**Features:**
- Quick filters via Choice-based dropdown (all/movies/series)
- **Advanced Modal Filtering:**
  - Content Type: movies, series, or all
  - Removed Status: yes, no, or all
  - Watched Status: yes, no, or all
  - Date Range: YYYY-MM-DD format (start and end date)
- Automatically excludes channel type (only shows movies/series)
- Shows removed status and flagged watched status
- Displays times watched, last watched date, time offset
- Paginated table view (10 items per page)
- Ephemeral messages (private to user)

**Modal Example:**
When using `/watched use_advanced: True`, a form opens with fields:
- Content Type: `movies`
- Removed Status: `yes`
- Watched Status: `all`
- Start Date: `2024-01-01`
- End Date: `2024-12-31`

Result: Shows all removed movies (watched or not) from 2024

**Key Components:**
- `WatchedCog` - Main command handler
- `WatchedPaginationView` - Simple pagination
- Direct Stremio API integration for library data

**Dependencies:**
- `models/user_auth.py`
- Stremio API (`https://api.strem.io/api/datastoreGet`)

---

### 🔧 admin.py
**Purpose:** Administrative and infrastructure monitoring

**Slash Commands:**
- `/status` - Check Docker container status (all users)
- `/ping` - Test bot responsiveness (admin only)
- `/restart container_name: <name>` - Restart a container (admin only)
- `/whoami` - Show your user ID and admin status (all users)

**Features:**
- Monitors configured Docker containers (optional)
- Different output for admin vs regular users:
  - **Regular users:** Simple "All OK" or "Issues detected" message
  - **Admin users:** Detailed container status list
- DM alerts to admin when services are down
- Color-coded status indicators (✅/❌)
- Disabled when no containers configured

**Monitored Containers:**
Configured in `.env` (comma-separated list):
```env
MONITORED_CONTAINERS=container1,container2,container3,...
```

Leave empty or unset to disable the `/status` command.

**Admin Setup:**
Set `ADMIN_USER_ID` in `.env` to enable admin-only commands

**Key Components:**
- `AdminCog` - Command handler
- Docker socket integration for container status
- DM notification system for failures

**Dependencies:**
- `/var/run/docker.sock` - Must be mounted in docker-compose.yml

---

### ❓ help.py
**Purpose:** Command documentation and help system

**Slash Commands:**
- `/help` - Display all available commands with descriptions

**Features:**
- Lists all slash commands from all cogs
- Organized by category (Search, Library, Admin, etc.)
- Shows parameter descriptions and examples
- Translatable help text via language system
- Ephemeral response (private to user)

**Key Components:**
- `HelpCog` - Simple help command handler
- Integrates with language system for translations

**Dependencies:**
- `utils/language.py`

---

## Creating a New Cog

### Template Structure

```python
"""Brief description of cog purpose."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.language import t
from models.user_auth import UserAuthManager

class MyCog(commands.Cog):
    """Cog description."""

    def __init__(self, bot, auth_manager: UserAuthManager = None):
        self.bot = bot
        self.auth_manager = auth_manager

    @app_commands.command(name="mycommand", description="What this command does")
    @app_commands.describe(arg="Description of the parameter")
    async def my_command(self, interaction: discord.Interaction, arg: str):
        """Command docstring."""
        # Defer response for long operations
        await interaction.response.defer(ephemeral=True)

        # Your command logic here
        result = await some_async_operation(arg)

        # Send response
        await interaction.followup.send(t('MY_RESPONSE_KEY'), ephemeral=True)

async def setup(bot, auth_manager: UserAuthManager = None):
    """Setup function called by bot.py"""
    await bot.add_cog(MyCog(bot, auth_manager))
```

### Best Practices

1. **Use ephemeral messages** - Add `ephemeral=True` for private responses
2. **Defer long operations** - Use `await interaction.response.defer()` for operations >3 seconds
3. **Leverage language system** - Use `t('KEY')` instead of hardcoded strings
4. **Handle errors gracefully** - Provide clear user feedback
5. **Add parameter descriptions** - Use `@app_commands.describe()` for all parameters
6. **Use Choices for predefined options** - Implement dropdown selectors with `@app_commands.choices()`
7. **Document commands** - Use descriptive `description` parameter and docstrings
8. **Use Modals for complex inputs** - Implement `discord.ui.Modal` for multi-field forms

### Adding Cog to Bot

Edit `bot.py` to load your cog:

```python
from cogs import my_cog

# In setup_hook():
await my_cog.setup(self, self.auth_manager)
print(t('COG_LOADED', cog='MyCog'))
```

## Architecture

### Cog Lifecycle

1. **Import** - Bot imports cog module
2. **Setup** - Calls `setup(bot, auth_manager)` function
3. **Registration** - Cog registers with bot via `add_cog()`
4. **Ready** - Commands become available
5. **Reload** - Cog can be hot-reloaded without restart

### Common Patterns

#### Authentication Required
```python
user_id = interaction.user.id
auth_key = self.auth_manager.get_auth_key(user_id)
if not auth_key:
    await interaction.response.send_message(t('ERROR_NOT_AUTHENTICATED'), ephemeral=True)
    return
```

#### Deferred Response (Long Operations)
```python
# Defer immediately for operations that take >3 seconds
await interaction.response.defer(ephemeral=True)

# ... do work ...

# Send response via followup
await interaction.followup.send(result, ephemeral=True)
```

#### Using Choices for Dropdowns
```python
@app_commands.command(name="filter", description="Filter content")
@app_commands.describe(type="Content type to filter")
@app_commands.choices(type=[
    app_commands.Choice(name="Movies", value="movie"),
    app_commands.Choice(name="TV Shows", value="series"),
    app_commands.Choice(name="All Content", value="all"),
])
async def filter_command(self, interaction: discord.Interaction, type: app_commands.Choice[str]):
    selected_type = type.value  # "movie", "series", or "all"
    # ... use selected_type ...
```

#### Error Handling
```python
try:
    # ... operation ...
except Exception as e:
    print(f"Error: {e}")
    if interaction.response.is_done():
        await interaction.followup.send(t('ERROR_GENERIC'), ephemeral=True)
    else:
        await interaction.response.send_message(t('ERROR_GENERIC'), ephemeral=True)
```

#### Admin Check Decorator
```python
from config import Config

def is_admin():
    """Check if user is admin"""
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id == Config.ADMIN_USER_ID
    return app_commands.check(predicate)

@app_commands.command(name="admin_command", description="Admin only")
@is_admin()
async def admin_command(self, interaction: discord.Interaction):
    # Only admin can use this
    pass
```

## Testing

Test individual cogs by running slash commands in Discord:

1. Ensure bot is running and commands are synced (check logs for "✅ Synced X slash command(s)")
2. Type `/` in Discord to see available commands with autocomplete
3. Test command with valid parameters
4. Check bot logs for errors: `docker logs stremiobot`
5. Verify ephemeral messages are private (only visible to you)
6. Test error cases (missing auth, invalid input, missing permissions)
7. Test Choices dropdowns work correctly
8. Test Modal forms submit and validate properly

## Dependencies

All cogs depend on:
- `discord.py==2.6.4` - Discord API wrapper with app_commands support
- `utils/language.py` - Translation system

Specific dependencies are listed per cog above.

## Slash Command Resources

- [discord.py App Commands Documentation](https://discordpy.readthedocs.io/en/stable/interactions/api.html)
- [Discord Slash Commands Guide](https://discord.com/developers/docs/interactions/application-commands)
- [App Commands Examples](https://github.com/Rapptz/discord.py/tree/master/examples/app_commands)
