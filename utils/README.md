# Utils Directory

Utility functions and helper modules used throughout the bot.

## Overview

This directory contains reusable utility functions that don't fit into specific domains (cogs, services, models). Utilities provide common functionality like language loading, formatting, and other helper operations.

## Available Utilities

### 🌍 language.py

**Purpose:** Multilingual support system for the bot

**Components:**
- `Language` class - Singleton for loading and managing translations
- `t()` function - Simple translation function

---

## Language System

### Architecture

The language system uses a singleton pattern to load translation files once at bot startup and provide fast key-value lookups throughout the application.

```
┌─────────────┐
│   bot.py    │
│ loads lang  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Language.load  │
│   (singleton)   │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│  ENGLISH.lang    │
│  or DUTCH.lang   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ In-memory dict   │
│  {KEY: "value"}  │
└────────┬─────────┘
         │
         ▼
    ┌───────────┐
    │ t("KEY")  │
    └───────────┘
```

### Language Class

#### Class Methods

##### `load(language: str = "ENGLISH") -> None`

Load a language file into memory.

**Parameters:**
- `language` (str) - Language name (uppercase, e.g., "ENGLISH", "DUTCH")

**Behavior:**
- Reads `lang/{language}.lang` file
- Parses key=value pairs
- Stores in class-level `_translations` dictionary
- Handles multi-line values
- Strips comments (lines starting with #)

**Example:**
```python
from utils.language import Language

# Load English
Language.load("ENGLISH")

# Load Dutch
Language.load("DUTCH")
```

**Error Handling:**
- Prints error if file not found
- Continues with empty translations (returns keys as-is)

---

##### `get(key: str, **kwargs) -> str`

Get a translated string with optional variable substitution.

**Parameters:**
- `key` (str) - Translation key (e.g., "HELP_TITLE")
- `**kwargs` - Variables to substitute in translation

**Returns:**
- Translated string with variables substituted
- Original key if translation not found

**Example:**
```python
# Simple translation
title = Language.get("HELP_TITLE")
# Returns: "Bot Commands" (if in ENGLISH.lang)

# With variables
message = Language.get("LIBRARY_ITEM_OF", current=5, total=25)
# Returns: "Item 5 of 25"

# Missing key
missing = Language.get("NONEXISTENT_KEY")
# Returns: "NONEXISTENT_KEY"
```

**Variable Substitution:**

Translation file:
```
GREETING=Hello {name}, you have {count} messages
```

Code:
```python
msg = Language.get("GREETING", name="Alice", count=3)
# Returns: "Hello Alice, you have 3 messages"
```

---

### t() Function

Shorthand convenience function for `Language.get()`.

**Signature:**
```python
def t(key: str, **kwargs) -> str
```

**Example:**
```python
from utils.language import t

# Instead of Language.get("KEY")
message = t("HELP_TITLE")

# With variables
message = t("LIBRARY_ITEM_OF", current=5, total=25)
```

**Usage in Bot:**
```python
import discord
from utils.language import t

# In embeds
embed = discord.Embed(
    title=t("HELP_TITLE"),
    description=t("HELP_DESCRIPTION"),
    color=discord.Color.blue()
)

# In messages
await ctx.send(t("ERROR_NOT_AUTHENTICATED"))

# With variables
await ctx.send(t("COG_LOADED", cog="Search"))
```

---

## File Format Details

### Parsing Rules

The language loader handles:

1. **Comments** - Lines starting with `#` are ignored
2. **Empty lines** - Ignored
3. **Key=Value pairs** - Split on first `=`
4. **Multi-line values** - Join lines until next key
5. **Whitespace** - Leading/trailing whitespace stripped from values

### Example Parsing

**Input file:**
```
# This is a comment
HELP_TITLE=Bot Commands

# Multi-line value
HELP_DESCRIPTION=Welcome to the bot!
This is line 2
This is line 3

ERROR_NOT_FOUND=Command not found
```

**Parsed result:**
```python
{
    "HELP_TITLE": "Bot Commands",
    "HELP_DESCRIPTION": "Welcome to the bot!\nThis is line 2\nThis is line 3",
    "ERROR_NOT_FOUND": "Command not found"
}
```

### Variable Substitution Format

Variables use Python's `str.format()` syntax:

**In translation file:**
```
MESSAGE=User {username} has {count} items
```

**In code:**
```python
result = t("MESSAGE", username="Alice", count=5)
# Returns: "User Alice has 5 items"
```

**Advanced formatting:**
```
# Numbers
PRICE=Price: ${amount:.2f}
# Usage: t("PRICE", amount=19.5) → "Price: $19.50"

# Dates (if passed as formatted string)
DATE=Last updated: {date}
# Usage: t("DATE", date="2024-01-15") → "Last updated: 2024-01-15"
```

---

## Usage Patterns

### In Cogs

```python
from discord.ext import commands
from utils.language import t

class MyCog(commands.Cog):
    @commands.command()
    async def greet(self, ctx, name: str):
        # Use t() for all user-facing text
        greeting = t("CUSTOM_GREETING", name=name)
        await ctx.send(greeting, ephemeral=True)
```

### In Embeds

```python
import discord
from utils.language import t

embed = discord.Embed(
    title=t("LIBRARY_TITLE"),
    description=t("LIBRARY_DESCRIPTION"),
    color=discord.Color.blue()
)

embed.add_field(
    name=t("FIELD_NAME"),
    value=t("FIELD_VALUE", count=10),
    inline=False
)

await ctx.send(embed=embed)
```

### In Views (UI Components)

```python
import discord
from utils.language import t

class MyView(discord.ui.View):
    def __init__(self):
        super().__init__()

        # Translate button labels
        self.add_button = discord.ui.Button(
            label=t("BUTTON_ADD"),
            style=discord.ButtonStyle.primary
        )
        self.add_button.callback = self.on_add
        self.add_item(self.add_button)
```

### Error Messages

```python
from utils.language import t

try:
    # ... operation ...
    await ctx.send(t("SUCCESS_MESSAGE"))
except Exception as e:
    print(f"Error: {e}")
    await ctx.send(t("ERROR_GENERIC"), ephemeral=True)
```

---

## Best Practices

### Do's ✅

1. **Always use t() for user-facing text**
   ```python
   # Good
   await ctx.send(t("WELCOME_MESSAGE"))

   # Bad
   await ctx.send("Welcome to the bot!")
   ```

2. **Use descriptive key names**
   ```python
   # Good
   t("ERROR_NOT_AUTHENTICATED")
   t("LIBRARY_EMPTY_MESSAGE")

   # Bad
   t("ERR1")
   t("MSG")
   ```

3. **Pass variables for dynamic content**
   ```python
   # Good
   t("USER_ITEMS", name="Alice", count=5)

   # Bad
   f"User Alice has {count} items"
   ```

4. **Group related keys**
   ```python
   HELP_TITLE=...
   HELP_DESCRIPTION=...
   HELP_SEARCH=...

   ERROR_NOT_FOUND=...
   ERROR_NOT_AUTHENTICATED=...
   ERROR_GENERIC=...
   ```

### Don'ts ❌

1. **Don't hardcode strings**
   ```python
   # Bad
   await ctx.send("Command not found")

   # Good
   await ctx.send(t("ERROR_COMMAND_NOT_FOUND"))
   ```

2. **Don't concatenate translations**
   ```python
   # Bad
   message = t("HELLO") + " " + t("WORLD")

   # Good (single key)
   message = t("HELLO_WORLD")
   ```

3. **Don't format before translation**
   ```python
   # Bad
   key = f"ERROR_{error_type}"
   t(key)

   # Good (use specific keys)
   if error_type == "auth":
       t("ERROR_NOT_AUTHENTICATED")
   ```

4. **Don't modify return values**
   ```python
   # Bad
   message = t("TITLE").upper()

   # Good (translation should include formatting)
   t("TITLE_UPPERCASE")
   ```

---

## Singleton Pattern

The Language class uses the singleton pattern:

```python
class Language:
    _translations = {}
    _language = "ENGLISH"

    @classmethod
    def load(cls, language: str):
        # Loads into class-level _translations
        cls._translations = {...}

    @classmethod
    def get(cls, key: str, **kwargs):
        # Accesses class-level _translations
        return cls._translations.get(key, key)
```

**Benefits:**
- Loaded once at startup
- No instantiation needed
- Fast dictionary lookups
- Low memory footprint

**Tradeoffs:**
- No runtime language switching per user
- All users see same language
- Requires bot restart to change language

---

## Extending the System

### Adding New Utility Functions

Create new files in `utils/` as needed:

**utils/formatters.py:**
```python
"""Formatting utilities."""

def format_duration(seconds: int) -> str:
    """Format seconds as HH:MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def truncate(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
```

**Usage:**
```python
from utils.formatters import format_duration, truncate

duration = format_duration(3665)  # "01:01:05"
short_name = truncate("Very Long Movie Title Here", 20)  # "Very Long Movie T..."
```

### Per-User Language Support (Future)

To support per-user languages:

1. **Store user language preference:**
   ```python
   # models/user_preferences.py
   class UserPreferences:
       def get_language(user_id: int) -> str:
           # Return "ENGLISH", "DUTCH", etc.
   ```

2. **Pass language to t():**
   ```python
   # Modified language.py
   def t(key: str, language: str = None, **kwargs) -> str:
       if language:
           translations = load_language(language)
       else:
           translations = Language._translations
       return translations.get(key, key).format(**kwargs)
   ```

3. **Use in commands:**
   ```python
   user_lang = UserPreferences.get_language(ctx.author.id)
   message = t("WELCOME", language=user_lang, name=ctx.author.name)
   ```

---

## Testing

### Unit Tests

```python
import unittest
from utils.language import Language, t

class TestLanguage(unittest.TestCase):
    def setUp(self):
        Language.load("ENGLISH")

    def test_simple_translation(self):
        result = t("HELP_TITLE")
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "HELP_TITLE")

    def test_variable_substitution(self):
        result = t("LIBRARY_ITEM_OF", current=5, total=10)
        self.assertIn("5", result)
        self.assertIn("10", result)

    def test_missing_key(self):
        result = t("NONEXISTENT_KEY")
        self.assertEqual(result, "NONEXISTENT_KEY")
```

### Integration Tests

```bash
# Load bot with different languages
export BOT_LANG=DUTCH
docker-compose up -d

# Test commands in Discord
# Verify responses are in Dutch

export BOT_LANG=ENGLISH
docker-compose restart

# Test commands again
# Verify responses are in English
```

---

## Performance Considerations

### Load Time
- Language files loaded once at startup
- Typical load time: <10ms for 84 keys
- Negligible impact on bot startup

### Memory Usage
- ~10-20 KB per language file in memory
- Dictionary lookups: O(1) complexity
- No significant memory impact

### Lookup Speed
- Direct dictionary access
- No parsing on each lookup
- Microsecond-level latency

---

## Dependencies

**Standard Library:**
- `os` - File operations
- `typing` - Type hints

No external dependencies required.

---

## Future Enhancements

- [ ] Hot reload language files without restart
- [ ] Per-user language preferences
- [ ] Language detection from Discord user locale
- [ ] Pluralization support (1 item vs 2 items)
- [ ] Date/time localization
- [ ] Number formatting per locale
- [ ] RTL (right-to-left) language support
- [ ] Translation validation (missing keys, unused keys)
- [ ] Language file compilation for faster loading
- [ ] Fallback language chain (e.g., FRENCH → ENGLISH)
