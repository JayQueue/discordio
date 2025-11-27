"""Hybrid metadata service: TMDB for search, aiometadata for posters."""
import requests
from typing import Optional
from config import Config

class TMDBService:
    """Service for fetching metadata.

    Uses TMDB API for searching content and getting IDs.
    Uses aiometadata API for fast poster fetching.
    """

    TMDB_BASE_URL = "https://api.themoviedb.org/3"

    @staticmethod
    def get_poster(item_id: str) -> Optional[str]:
        """Get poster URL for a given item ID using aiometadata."""
        if not item_id:
            print(f"⚠️ get_poster: No item_id provided")
            return None

        item_id_str = str(item_id)
        print(f"🔍 Fetching poster for: {item_id_str}")

        # Parse item_id format: prefix:id or just id
        if ':' in item_id_str:
            prefix, actual_id = item_id_str.split(':', 1)
            item_id_str = actual_id
            print(f"   Parsed ID: {actual_id} (prefix: {prefix})")

        # Determine content type based on ID format
        if item_id_str.startswith('tt'):
            # IMDb ID - try both movie and series
            print(f"   Detected IMDb ID, trying movie first...")
            poster = TMDBService._get_metadata(item_id_str, "movie")
            if not poster:
                print(f"   Not found as movie, trying series...")
                poster = TMDBService._get_metadata(item_id_str, "series")
            if poster:
                print(f"   ✅ Poster found: {poster[:80]}...")
            else:
                print(f"   ❌ No poster found for {item_id_str}")
            return poster
        else:
            # TMDB ID - try both formats
            print(f"   Detected TMDB ID, trying movie first...")
            poster = TMDBService._get_metadata(f"tmdb:{item_id_str}", "movie")
            if not poster:
                print(f"   Not found as movie, trying series...")
                poster = TMDBService._get_metadata(f"tmdb:{item_id_str}", "series")
            if poster:
                print(f"   ✅ Poster found: {poster[:80]}...")
            else:
                print(f"   ❌ No poster found for tmdb:{item_id_str}")
            return poster

    @staticmethod
    def _get_metadata(item_id: str, content_type: str = "movie") -> Optional[str]:
        """Get poster from aiometadata API using /poster endpoint with enhanced parameters.

        Falls back to direct TMDB if metadata service is unavailable and TMDB_API_KEY is set.
        Uses TMDB directly if METADATA_URL is not configured.
        """
        # If no metadata service configured, use TMDB directly
        if not Config.METADATA_URL:
            print(f"      ℹ️ No metadata service configured, using direct TMDB")
            if Config.TMDB_API_KEY and item_id.startswith('tmdb:'):
                tmdb_id = item_id.split(':', 1)[1]
                poster_path = TMDBService._get_tmdb_poster_path(tmdb_id, content_type)
                if poster_path:
                    fallback_url = f"https://image.tmdb.org/t/p/w600_and_h900_bestv2{poster_path}"
                    print(f"      ✅ Direct TMDB: {fallback_url[:80]}...")
                    return fallback_url
            print(f"      ❌ TMDB_API_KEY not set or not a TMDB ID")
            return None

        try:
            from urllib.parse import quote

            # aiometadata /poster endpoint expects tmdb:ID format for TMDB IDs
            # or just tt123456 for IMDb IDs
            base_url = f"{Config.METADATA_URL}/poster/{content_type}/{item_id}"

            # Build query parameters for better poster quality
            params = {
                'lang': 'en-US',  # Language preference
                'key': Config.RPDB_KEY  # Poster database key for rpdb (configurable)
            }

            # Try to build TMDB fallback URL for better coverage
            # Extract numeric ID if it's a TMDB ID
            tmdb_fallback_url = None
            if item_id.startswith('tmdb:'):
                tmdb_id = item_id.split(':', 1)[1]
                if Config.TMDB_API_KEY:
                    # Get poster path from TMDB
                    poster_path = TMDBService._get_tmdb_poster_path(tmdb_id, content_type)
                    if poster_path:
                        tmdb_fallback_url = f"https://image.tmdb.org/t/p/w600_and_h900_bestv2{poster_path}"
                        params['fallback'] = tmdb_fallback_url

            # Build URL with query parameters
            query_string = '&'.join([f"{k}={quote(str(v))}" for k, v in params.items()])
            url = f"{base_url}?{query_string}"
            print(f"      API call: {url}")

            # The /poster endpoint returns the image URL or redirects
            response = requests.get(url, timeout=5, allow_redirects=False)
            print(f"      Response: {response.status_code}")

            if response.status_code in [200, 301, 302, 307, 308]:
                # If it's a redirect, get the Location header
                if response.status_code in [301, 302, 307, 308]:
                    poster_url = response.headers.get('Location')
                    if poster_url:
                        print(f"      ✅ Redirect to: {poster_url[:80]}...")
                        return poster_url
                # If it's 200, the response itself might contain the URL
                poster_url = response.url if hasattr(response, 'url') else url
                print(f"      ✅ Poster URL: {poster_url[:80]}...")
                return poster_url
            elif response.status_code == 404:
                print(f"      404 - Item not found in metadata")
            else:
                print(f"      Unexpected status: {response.status_code}")
        except (requests.ConnectionError, requests.Timeout) as e:
            # Metadata service unavailable - fall back to direct TMDB
            print(f"      ⚠️ Metadata service unavailable: {e}")
            if tmdb_fallback_url:
                print(f"      🔄 Using direct TMDB fallback: {tmdb_fallback_url[:80]}...")
                return tmdb_fallback_url
            elif Config.TMDB_API_KEY and item_id.startswith('tmdb:'):
                # Try to fetch TMDB poster path now as a last resort
                print(f"      🔄 Attempting direct TMDB fetch as fallback...")
                tmdb_id = item_id.split(':', 1)[1]
                poster_path = TMDBService._get_tmdb_poster_path(tmdb_id, content_type)
                if poster_path:
                    fallback_url = f"https://image.tmdb.org/t/p/w600_and_h900_bestv2{poster_path}"
                    print(f"      ✅ Direct TMDB fallback: {fallback_url[:80]}...")
                    return fallback_url
            print(f"      ❌ No fallback available (TMDB_API_KEY not set or not a TMDB ID)")
        except Exception as e:
            print(f"      ⚠️ Metadata fetch error for {item_id}: {e}")

        return None

    @staticmethod
    def _get_tmdb_poster_path(tmdb_id: str, content_type: str = "movie") -> Optional[str]:
        """Get poster path from TMDB API for fallback URL construction."""
        if not Config.TMDB_API_KEY:
            return None

        try:
            media_type = "movie" if content_type == "movie" else "tv"
            url = f"{TMDBService.TMDB_BASE_URL}/{media_type}/{tmdb_id}"
            params = {"api_key": Config.TMDB_API_KEY}

            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('poster_path')
        except Exception as e:
            print(f"      TMDB poster path fetch error: {e}")

        return None

    @staticmethod
    def search_title(title: str, content_type: str = "movie") -> Optional[str]:
        """Search TMDB for a title and return the best-matching ID.

        Uses TMDB API for search, returns IMDb ID or TMDB ID.
        """
        if not Config.TMDB_API_KEY:
            print("Warning: TMDB_API_KEY not set, search unavailable")
            return None

        search_type = "movie" if content_type == "movie" else "tv"
        url = f"{TMDBService.TMDB_BASE_URL}/search/{search_type}"
        params = {
            "api_key": Config.TMDB_API_KEY,
            "query": title,
            "language": Config.BOT_LANG.lower() if hasattr(Config, 'BOT_LANG') else "en-US"
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                results = response.json().get('results', [])
                if results:
                    tmdb_id = results[0].get('id')

                    # Try to get IMDb ID from external IDs endpoint
                    detail_url = f"{TMDBService.TMDB_BASE_URL}/{search_type}/{tmdb_id}/external_ids"
                    detail_response = requests.get(detail_url, params={"api_key": Config.TMDB_API_KEY}, timeout=5)

                    if detail_response.status_code == 200:
                        imdb_id = detail_response.json().get('imdb_id')
                        if imdb_id:
                            return imdb_id

                    # Fall back to TMDB ID if no IMDb ID found
                    return f"tmdb:{tmdb_id}"
        except Exception as e:
            print(f"TMDB search error: {e}")

        return None
