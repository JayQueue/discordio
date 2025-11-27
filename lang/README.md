# Lang Directory

Translation files for multilingual bot support.

## Overview

The language system enables the bot to support multiple languages through simple key-value translation files. All user-facing text is abstracted into language keys that can be translated independently.

## Available Languages

### ENGLISH.lang
- Default language
- All keys documented with clear English text
- Used as reference for creating new translations

### DUTCH.lang
- Complete Dutch translation
- Includes all 84+ translation keys
- Dutch aliases for commands

## File Format

### Syntax

```
# Comment lines start with #
KEY=Value text here
MULTI_LINE=First line\nSecond line
WITH_VARIABLE=Hello {name}, you have {count} items
```

### Rules

1. **Comments** - Lines starting with `#` are ignored
2. **Key Format** - UPPERCASE_WITH_UNDERSCORES
3. **No Quotes** - Values are plain text (no quotes needed)
4. **Multi-line** - Use `\n` for line breaks
5. **Variables** - Use `{variable_name}` for substitution
6. **Encoding** - UTF-8 encoding required

### Example

```
# Help Command
HELP_TITLE=Bot Commands
HELP_DESCRIPTION=Here are all available commands:
HELP_SEARCH=🔍 **Search**\n• `!film <query>` - Search movies\n• `!serie <query>` - Search series

# Errors
ERROR_NOT_AUTHENTICATED=You need to authenticate first. Send me `!setauth <key>` in a DM.
ERROR_COMMAND_NOT_FOUND=Unknown command. Use `!help` for available commands.

# With Variables
LIBRARY_ITEM_OF=Item {current} of {total}
COG_LOADED=✅ {cog} cog loaded successfully
```

## Translation Keys

### Categories

The bot uses 84+ translation keys organized into categories:

#### Initialization (INIT_*)
- `INIT_BOT` - Bot initialization message
- `INIT_SUCCESS` - Initialization success

#### Loading (LOADING_*)
- `LOADING_COGS` - Loading cogs message
- `LOADING_LIBRARY` - Loading library indicator
- `LOADING_SEARCH_COG` - Individual cog load messages

#### Commands (HELP_*, SEARCH_*, LIBRARY_*, etc.)
- Help text and command descriptions
- Success/failure messages
- User prompts

#### Errors (ERROR_*)
- Authentication errors
- Command errors
- API errors

#### Status Messages (STATUS_*, ADMIN_*)
- Container status
- Service health
- Admin alerts

#### UI Elements (BUTTON_*, SELECT_*)
- Button labels
- Dropdown placeholders
- Pagination controls

#### Item Details (ITEM_*, TYPE_*)
- Library item fields
- Content type labels
- Status indicators

## Usage in Code

### Basic Translation

```python
from utils.language import t

# Simple translation
message = t('HELP_TITLE')

# With variables
message = t('LIBRARY_ITEM_OF', current=5, total=25)
message = t('COG_LOADED', cog='Search')
```

### In Discord Commands

```python
@commands.command(name="help")
async def help_command(self, ctx):
    embed = discord.Embed(
        title=t('HELP_TITLE'),
        description=t('HELP_DESCRIPTION'),
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)
```

## Creating a New Language

### Step 1: Copy Template

```bash
cp lang/ENGLISH.lang lang/FRENCH.lang
```

### Step 2: Translate Values

Edit `FRENCH.lang` and translate all values, keeping keys unchanged:

```
# BEFORE (English)
HELP_TITLE=Bot Commands
ERROR_NOT_AUTHENTICATED=You need to authenticate first.

# AFTER (French)
HELP_TITLE=Commandes du Bot
ERROR_NOT_AUTHENTICATED=Vous devez d'abord vous authentifier.
```

### Step 3: Configure Bot

Update `.env`:
```env
BOT_LANG=FRENCH
```

### Step 4: Test

1. Restart bot: `docker-compose restart`
2. Test commands in Discord
3. Verify all text appears in French

### Step 5: (Optional) Add to Language Selector

Update `services/gemini.py` to include language name:

```python
language_names = {
    "ENGLISH": "English",
    "DUTCH": "Dutch",
    "FRENCH": "French",  # Add this
    "GERMAN": "German",
    "SPANISH": "Spanish"
}
```

## Translation Guidelines

### Best Practices

1. **Keep tone consistent** - Match the original tone (friendly, professional, etc.)
2. **Preserve formatting** - Keep `\n`, `**bold**`, and markdown formatting
3. **Test variables** - Ensure `{variable}` placeholders make sense in translation
4. **Cultural adaptation** - Adapt idioms and expressions when needed
5. **Unicode support** - Use proper characters (é, ñ, ü, etc.)
6. **Length awareness** - Discord embeds have character limits
7. **Command names** - Only translate help text, not actual command names

### Variable Guidelines

Variables must remain unchanged in translations:

```
# CORRECT
ENGLISH: Hello {name}, you have {count} messages
FRENCH:  Bonjour {name}, vous avez {count} messages

# WRONG - Variable names changed
FRENCH:  Bonjour {nom}, vous avez {nombre} messages
```

### Formatting Preservation

Keep Discord markdown formatting:

```
# CORRECT
ENGLISH: **Bold** text and `code` formatting
FRENCH:  Texte en **gras** et formatage `code`

# WRONG - Formatting lost
FRENCH:  Texte en gras et formatage code
```

## Language System Architecture

### Loading Process

1. Bot reads `BOT_LANG` from config
2. `Language.load()` called in `bot.py`
3. Corresponding `.lang` file parsed
4. Keys stored in memory dictionary
5. `t()` function retrieves translations

### Fallback Behavior

If a key is missing:
```python
# Returns: "MISSING_KEY"
t('MISSING_KEY')

# With variables
# Returns: "MISSING_KEY (arg1=value1)"
t('MISSING_KEY', arg1='value1')
```

### Hot Reload

Language files are loaded at bot startup. To reload:
```bash
docker-compose restart
```

## Complete Key Reference

### Required Keys

All language files must include these 84+ keys:

#### Core
- `INIT_BOT`, `INIT_SUCCESS`
- `LOADING_COGS`, `ALL_COGS_LOADED`
- `BOT_READY`, `LOGGED_IN_AS`

#### Help
- `HELP_TITLE`, `HELP_DESCRIPTION`
- `HELP_SEARCH`, `HELP_LIBRARY`, `HELP_ADMIN`, `HELP_AUTH`

#### Search
- `SEARCH_MOVIES`, `SEARCH_SERIES`
- `SELECT_MOVIE`, `SELECT_SERIES`

#### Library
- `LIBRARY_EMPTY`, `LIBRARY_PAGE`
- `LIBRARY_TOTAL_ITEMS`, `LIBRARY_ITEM_OF`

#### Watched
- Commands and filters for watched items

#### Errors
- `ERROR_NOT_AUTHENTICATED`, `ERROR_COMMAND_NOT_FOUND`
- `ERROR_NO_RESULTS`, `ERROR_GENERIC`

#### Status
- `ADMIN_STATUS_ALL_OK`, `ADMIN_STATUS_ISSUES`
- `STATUS_WATCHED`, `STATUS_NOT_WATCHED`

#### UI
- `BUTTON_ADD`, `BUTTON_CANCEL`
- `BUTTON_PREVIOUS`, `BUTTON_NEXT`

See `ENGLISH.lang` for the complete list and documentation.

## Troubleshooting

### Bot shows "MISSING_KEY" in messages
**Cause:** Key not found in language file
**Fix:** Add missing key to your `.lang` file

### Text appears in wrong language
**Cause:** `BOT_LANG` not set correctly
**Fix:** Check `.env` and `docker-compose.yml` environment

### Special characters broken
**Cause:** File encoding issue
**Fix:** Ensure `.lang` file is UTF-8 encoded

### Variables not substituting
**Cause:** Variable name mismatch in code
**Fix:** Check code calls `t()` with correct variable names

## Contributing Translations

To contribute a new language:

1. Fork the repository
2. Create `lang/YOURLANG.lang`
3. Translate all keys from `ENGLISH.lang`
4. Test thoroughly
5. Submit pull request

Include in PR:
- Complete translation file
- Test results showing all commands work
- Native speaker verification (if possible)
