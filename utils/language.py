"""Language management system for multilingual support."""
import os
from typing import Dict, Optional

class Language:
    """
    Handles loading and accessing translation strings from .lang files.

    The .lang file format is simple:
    KEY=Translation text here
    MULTILINE_KEY=Line 1
        Line 2
        Line 3

    Lines starting with # are comments and ignored.
    Empty lines are ignored.
    """

    _instance: Optional['Language'] = None
    _strings: Dict[str, str] = {}
    _language: str = "ENGLISH"

    def __new__(cls):
        """Singleton pattern to ensure only one language instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load(cls, language: str = "ENGLISH") -> None:
        """
        Load translations from a .lang file in the lang folder.

        Args:
            language: The language name (without .lang extension)
        """
        cls._language = language.upper()
        lang_file = f"lang/{cls._language}.lang"

        if not os.path.exists(lang_file):
            raise FileNotFoundError(
                f"Language file '{lang_file}' not found. "
                f"Please create it in the lang folder or check your LANG setting in .env"
            )

        cls._strings = {}
        current_key = None
        current_value = []

        with open(lang_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n\r')

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Check if this is a new key=value pair
                if '=' in line and not line.startswith(' ') and not line.startswith('\t'):
                    # Save previous key if exists
                    if current_key:
                        cls._strings[current_key] = '\n'.join(current_value)

                    # Parse new key=value
                    key, value = line.split('=', 1)
                    current_key = key.strip()
                    current_value = [value]
                else:
                    # This is a continuation line (multiline value)
                    if current_key:
                        current_value.append(line)

        # Save the last key
        if current_key:
            cls._strings[current_key] = '\n'.join(current_value)

        print(f"✅ Loaded {len(cls._strings)} translations from {lang_file}")

    @classmethod
    def get(cls, key: str, **kwargs) -> str:
        """
        Get a translated string by key.

        Args:
            key: The translation key
            **kwargs: Optional format parameters for string formatting

        Returns:
            The translated string, or the key itself if not found
        """
        text = cls._strings.get(key, f"[MISSING: {key}]")

        # Apply string formatting if kwargs provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError as e:
                print(f"⚠️ Warning: Missing format parameter {e} for key '{key}'")

        return text

    @classmethod
    def current_language(cls) -> str:
        """Get the currently loaded language name."""
        return cls._language


# Convenience function for easy access
def t(key: str, **kwargs) -> str:
    """
    Shorthand function to get a translation.

    Usage:
        from utils.language import t
        message = t('WELCOME_MESSAGE', username="John")

    Args:
        key: The translation key
        **kwargs: Optional format parameters

    Returns:
        The translated string
    """
    return Language.get(key, **kwargs)
