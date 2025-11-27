# Services Directory

External service integrations and API wrappers.

## Overview

Services abstract external API interactions and provide a clean interface for cogs to use. Each service handles a specific integration (AI, metadata, etc.) with proper error handling and rate limiting awareness.

## Available Services

### 🤖 gemini.py

**Purpose:** Google Gemini AI integration for content recommendations

**Class:** `GeminiService`

#### Features

- AI-powered movie and TV show recommendations
- Language-aware responses (respects `BOT_LANG` configuration)
- Context-aware prompts for better suggestions
- Error handling with graceful fallbacks
- Streaming response support

#### Configuration

Set in `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get API key from: https://makersuite.google.com/app/apikey

#### API Reference

##### `get_recommendations(query: str, media_type: str = "movie") -> Optional[str]`

Get AI-powered recommendations for a search query.

**Parameters:**
- `query` (str) - User's search query (e.g., "sci-fi action movies")
- `media_type` (str) - Content type: `"movie"` or `"series"` (default: `"movie"`)

**Returns:**
- AI-generated recommendations (string) if successful
- `None` if API call fails

**Example:**
```python
from services.gemini import GeminiService

recommendations = GeminiService.get_recommendations(
    "space exploration sci-fi",
    media_type="movie"
)
# Returns: "Based on your interest in space exploration sci-fi, I recommend:
#          1. Interstellar (2014) - Epic journey through space and time..."
```

#### Prompt Engineering

The service uses carefully crafted prompts:

**Movie Prompt:**
```
You are a movie recommendation assistant.
Respond in {language}.
Based on the query "{query}", suggest 5 movies.
For each movie, provide:
- Title and year
- Brief description (1-2 sentences)
- Why it matches the query

Format as numbered list.
```

**Series Prompt:**
```
You are a TV show recommendation assistant.
Respond in {language}.
Based on the query "{query}", suggest 5 TV series.
For each series, provide:
- Title and year
- Brief description (1-2 sentences)
- Why it matches the query

Format as numbered list.
```

#### Language Support

Automatically adapts responses to configured bot language:

```python
# In config: BOT_LANG=DUTCH
recommendations = GeminiService.get_recommendations("action", "movie")
# AI responds in Dutch

# In config: BOT_LANG=ENGLISH
recommendations = GeminiService.get_recommendations("action", "movie")
# AI responds in English
```

Supported language mapping:
- `ENGLISH` → English
- `DUTCH` → Dutch
- `FRENCH` → French
- `GERMAN` → German
- `SPANISH` → Spanish

#### Error Handling

```python
try:
    recommendations = GeminiService.get_recommendations(query, media_type)
    if recommendations:
        # Success - show recommendations
        await ctx.send(recommendations)
    else:
        # API failed - show fallback message
        await ctx.send("Unable to get recommendations. Please try again.")
except Exception as e:
    print(f"Gemini error: {e}")
    await ctx.send("An error occurred. Please try again later.")
```

#### Rate Limits

Google Gemini API rate limits (as of 2024):
- Free tier: 60 requests per minute
- Standard tier: Higher limits with API key

The service doesn't implement rate limiting internally - rely on API error responses.

#### Best Practices

1. **Cache responses** for identical queries (not implemented - future enhancement)
2. **Validate media_type** before calling (only "movie" or "series")
3. **Handle None returns** gracefully
4. **Log errors** for debugging
5. **Keep prompts focused** for better results

---

### 🖼️ tmdb.py

**Purpose:** Hybrid metadata service - TMDB for search, aiometadata for posters

**Class:** `TMDBService`

**Note:** This service uses a hybrid approach:
- **TMDB API** for searching and finding content IDs
- **aiometadata API** for fast, local poster fetching with RPDB support

#### Features

- Fast poster fetching from local aiometadata instance
- **RPDB (Rating Poster Database) integration** for enhanced poster quality
- **Automatic TMDB fallback** when metadata service is unavailable
- Smart fallback URL generation from TMDB
- Language-aware poster selection (defaults to en-US)
- No external API rate limits
- Supports both IMDb IDs (tt1234567) and TMDB IDs (tmdb:12345)
- Automatic content type detection (movie vs series)
- Fallback between movie and series endpoints
- Resilient error handling with graceful degradation

#### Configuration

Set in `.env`:
```env
METADATA_URL=http://metadata:1337
RPDB_KEY=t0-free-rpdb        # RPDB poster database key
TMDB_API_KEY=your_tmdb_key   # Optional: for fallback poster URLs
```

**METADATA_URL:** Assumes aiometadata runs in Docker network with container name `metadata`.

**RPDB_KEY:**
- Default: `t0-free-rpdb` (free tier, works for most use cases)
- Premium: Custom RPDB API key for higher quality/more poster variants
- Learn more: [RPDB.dev](https://ratingposterdb.com/)

**TMDB_API_KEY:** Optional but recommended. Used to generate fallback poster URLs when RPDB doesn't have a poster.

#### API Reference

##### `get_poster(item_id: str) -> Optional[str]`

Fetch poster URL for a given content item.

**Parameters:**
- `item_id` (str) - Content identifier in one of these formats:
  - IMDb ID: `"tt1234567"`
  - TMDB ID: `"tmdb:12345"`
  - Prefixed: `"tt:1234567"` or `"tmdb:12345"`

**Returns:**
- Poster URL (string) if found
- `None` if not found or error

**Example:**
```python
from services.tmdb import TMDBService

# IMDb ID
poster_url = TMDBService.get_poster("tt0468569")
# Returns: "http://metadata:1337/poster/movie/tt0468569?lang=en-US&key=t0-free-rpdb&fallback=..."

# TMDB ID with enhanced parameters
poster_url = TMDBService.get_poster("tmdb:155")
# Returns: "http://metadata:1337/poster/movie/tmdb:155?lang=en-US&key=t0-free-rpdb&fallback=..."

# Not found
poster_url = TMDBService.get_poster("invalid_id")
# Returns: None
```

**Enhanced Poster URLs:**
The service generates URLs with query parameters for better coverage:
- `lang=en-US` - Language preference for poster selection
- `key=t0-free-rpdb` - RPDB database key (configurable via `RPDB_KEY`)
- `fallback=https://image.tmdb.org/t/p/w600_and_h900_bestv2/...` - TMDB fallback URL

##### `search_title(title: str, content_type: str = "movie") -> Optional[str]`

Search for a title and return its ID.

**Note:** This method currently returns `None` as aiometadata doesn't provide a direct search endpoint. Use Stremio's search or implement catalog browsing if needed.

**Parameters:**
- `title` (str) - Title to search for
- `content_type` (str) - Content type: `"movie"` or `"series"`

**Returns:**
- `None` (not implemented)

#### ID Format Handling

The service intelligently handles different ID formats:

```python
# All these work the same:
get_poster("tt0468569")      # IMDb format
get_poster("tt:0468569")     # Prefixed IMDb
get_poster("tmdb:155")       # Prefixed TMDB
get_poster("155")            # Plain TMDB (tries as TMDB)
```

#### Metadata API Integration

Uses aiometadata's poster endpoint with enhanced parameters:

```
GET {METADATA_URL}/poster/{type}/{id}?lang={lang}&key={rpdb_key}&fallback={encoded_url}

# Examples:
GET http://metadata:1337/poster/movie/tt0468569?lang=en-US&key=t0-free-rpdb&fallback=...
GET http://metadata:1337/poster/series/tmdb:1399?lang=en-US&key=t0-free-rpdb&fallback=...
```

**Query Parameters:**
- `lang` - Language code (e.g., `en-US`) for language-aware poster selection
- `key` - RPDB API key for enhanced poster quality from Rating Poster Database
- `fallback` - URL-encoded TMDB poster URL as fallback when RPDB doesn't have the poster

**Response:**
The endpoint returns a 302 redirect to the actual poster URL, which could be:
1. RPDB poster (if available and key is valid)
2. Fallback TMDB poster (if provided and RPDB unavailable)
3. aiometadata's own cached poster

**Legacy Meta Endpoint:**
The old meta endpoint still works but is not recommended:
```
GET {METADATA_URL}/meta/{type}/{id}.json
```

#### Fallback Logic

**Multi-tier fallback system for maximum reliability:**

1. **Content Type Fallback** - Tries both movie and series:
```python
def get_poster(item_id):
    # Try as movie first
    poster = _get_metadata(item_id, "movie")
    if poster:
        return poster

    # Fall back to series
    poster = _get_metadata(item_id, "series")
    return poster  # None if not found
```

2. **Service Fallback** - Direct TMDB when metadata service is down:
```python
def _get_metadata(item_id, content_type):
    try:
        # Try metadata service first (RPDB + aiometadata)
        response = requests.get(metadata_url, timeout=5)
        return poster_url
    except (ConnectionError, Timeout):
        # Metadata service unavailable - fall back to direct TMDB
        if TMDB_API_KEY and item_id.startswith('tmdb:'):
            poster_path = _get_tmdb_poster_path(tmdb_id, content_type)
            return f"https://image.tmdb.org/t/p/w600_and_h900_bestv2{poster_path}"
        return None
```

**Fallback Priority:**
1. aiometadata with RPDB (best quality)
2. aiometadata with TMDB fallback parameter
3. Direct TMDB API (if metadata service down)
4. None (if all methods fail)

#### Error Handling

```python
try:
    poster_url = TMDBService.get_poster(item_id)
    if poster_url:
        embed.set_image(url=poster_url)
    else:
        # No poster available - use default or skip
        pass
except Exception as e:
    print(f"Poster fetch error: {e}")
    # Continue without poster
```

Common errors:
- **Connection timeout** - Metadata service unreachable
- **404 Not Found** - Invalid ID or content not in database
- **500 Server Error** - Metadata service issue

#### Performance

- **Caching:** aiometadata caches responses for 24 hours
- **Timeout:** 5-second timeout per request
- **Concurrency:** No built-in rate limiting (local service)

#### Best Practices

1. **Always handle None** returns
2. **Don't block on poster fetches** - continue if unavailable
3. **Use short timeouts** (5s default is good)
4. **Log errors** for debugging metadata service issues
5. **Verify metadata container** is running and accessible

---

## Service Architecture

### Design Patterns

#### Singleton Pattern (Static Methods)

Services use static methods since they're stateless:

```python
class MyService:
    @staticmethod
    def do_something():
        # No instance needed
        pass

# Usage
result = MyService.do_something()
```

#### Error Isolation

Services handle their own errors and return `None` on failure:

```python
@staticmethod
def fetch_data():
    try:
        # API call
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None
```

#### Configuration Injection

Services read configuration from `config.py`:

```python
from config import Config

class MyService:
    @staticmethod
    def call_api():
        api_key = Config.MY_API_KEY
        url = Config.MY_API_URL
        # ...
```

## Creating a New Service

### Template

```python
"""Brief description of service."""
import requests
from typing import Optional
from config import Config

class MyService:
    """Service for integrating with XYZ API."""

    BASE_URL = "https://api.example.com"

    @staticmethod
    def get_data(query: str) -> Optional[dict]:
        """Fetch data from XYZ API.

        Args:
            query: Search query

        Returns:
            Data dictionary if successful, None otherwise
        """
        try:
            url = f"{MyService.BASE_URL}/search"
            params = {
                "q": query,
                "api_key": Config.XYZ_API_KEY
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"API error: {response.status_code}")
                return None

        except Exception as e:
            print(f"Service error: {e}")
            return None
```

### Adding to Config

Edit `config.py`:

```python
class Config:
    # ...
    XYZ_API_KEY: str = os.getenv("XYZ_API_KEY", "")
    XYZ_API_URL: str = os.getenv("XYZ_API_URL", "https://api.example.com")

    @classmethod
    def load(cls):
        # ...
        if not cls.XYZ_API_KEY:
            raise ValueError("XYZ_API_KEY must be set")
```

### Using in Cog

```python
from services.my_service import MyService

class MyCog(commands.Cog):
    @commands.command()
    async def search(self, ctx, query: str):
        data = MyService.get_data(query)

        if data:
            await ctx.send(f"Found: {data}")
        else:
            await ctx.send("No results found")
```

## Testing Services

### Manual Testing

```python
# test_service.py
from services.gemini import GeminiService
from services.tmdb import TMDBService

# Test Gemini
recs = GeminiService.get_recommendations("action movies", "movie")
print(recs)

# Test TMDB/Metadata
poster = TMDBService.get_poster("tt0468569")
print(poster)
```

Run:
```bash
python test_service.py
```

### Unit Testing

```python
import unittest
from unittest.mock import patch
from services.gemini import GeminiService

class TestGeminiService(unittest.TestCase):
    @patch('services.gemini.genai.GenerativeModel')
    def test_get_recommendations(self, mock_model):
        # Mock API response
        mock_model.return_value.generate_content.return_value.text = "1. Movie One\n2. Movie Two"

        result = GeminiService.get_recommendations("action", "movie")

        self.assertIsNotNone(result)
        self.assertIn("Movie One", result)
```

## Dependencies

### Required Packages

```txt
requests==2.31.0           # HTTP client
google-generativeai==0.3.0 # Gemini AI SDK
```

Install:
```bash
pip install -r requirements.txt
```

### External Services

- **Google Gemini AI** - Cloud-based AI service
- **aiometadata** - Local metadata service (Docker container)

## Troubleshooting

### Gemini API Errors

**Error:** `API key not valid`
- **Fix:** Check `GEMINI_API_KEY` in `.env`
- **Fix:** Generate new key from Google AI Studio

**Error:** `429 Too Many Requests`
- **Cause:** Rate limit exceeded
- **Fix:** Implement request throttling or upgrade API tier

### Metadata Service Errors

**Error:** `Connection refused`
- **Cause:** Metadata container not running
- **Fix:** `docker ps | grep metadata`

**Error:** `404 Not Found`
- **Cause:** Invalid ID or content not in database
- **Fix:** Verify ID format (tt1234567 or tmdb:12345)

**Error:** `Timeout after 5s`
- **Cause:** Metadata service slow or unresponsive
- **Fix:** Check metadata container logs, restart if needed

## Future Enhancements

- [ ] Response caching for Gemini (reduce API costs)
- [ ] Retry logic with exponential backoff
- [ ] Batch poster fetching for better performance
- [ ] Metadata search implementation via catalogs
- [ ] Alternative metadata providers (OMDB, Fanart.tv)
- [ ] Rate limiting for external APIs
- [ ] Circuit breaker pattern for service failures
- [ ] Metrics collection (request counts, latencies)
