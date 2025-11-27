"""Stremio API service for interacting with Stremio's datastore."""
import requests
from typing import Optional, Tuple, Dict, List
from datetime import datetime, timezone

class StremioService:
    """Service class for Stremio API interactions."""
    
    BASE_URL = "https://api.strem.io/api"
    
    @staticmethod
    def get_library(auth_key: str) -> Optional[Dict]:
        """Fetch all library items for a given auth key."""
        url = f"{StremioService.BASE_URL}/datastoreGet"
        payload = {
            "authKey": auth_key,
            "collection": "libraryItem",
            "all": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Stremio API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Exception fetching Stremio library: {e}")
            return None
    
    @staticmethod
    def get_active_items(auth_key: str) -> List[Dict]:
        """Get only non-removed items from the library."""
        library = StremioService.get_library(auth_key)
        if library:
            all_items = library.get('result', [])
            return [item for item in all_items if not item.get('removed', False)]
        return []
    
    @staticmethod
    def add_to_library(auth_key: str, item_id: str, item_type: str, name: str) -> Tuple[bool, str]:
        """Add an item to a user's Stremio library."""
        url = f"{StremioService.BASE_URL}/datastorePut"
        current_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        payload = {
            "authKey": auth_key,
            "collection": "libraryItem",
            "changes": [
                {
                    "_id": item_id,
                    "name": name,
                    "type": item_type,
                    "removed": False,
                    "temp": False,
                    "_ctime": current_time,
                    "_mtime": current_time
                }
            ]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            print(f"Stremio API response: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                return True, "Succesvol toegevoegd aan bibliotheek!"
            else:
                return False, f"API error: {response.status_code}"
        except Exception as e:
            print(f"Exception adding to library: {e}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def remove_from_library(auth_key: str, item_id: str, item_type: str, name: str) -> Tuple[bool, str]:
        """Remove an item from a user's Stremio library by marking it as removed."""
        url = f"{StremioService.BASE_URL}/datastorePut"
        current_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        payload = {
            "authKey": auth_key,
            "collection": "libraryItem",
            "changes": [
                {
                    "_id": item_id,
                    "name": name,
                    "type": item_type,
                    "removed": True,  # Mark as removed
                    "_mtime": current_time
                }
            ]
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            print(f"Stremio remove API response: {response.status_code} - {response.text}")

            if response.status_code == 200:
                return True, "Successfully removed from library!"
            else:
                return False, f"API error: {response.status_code}"
        except Exception as e:
            print(f"Exception removing from library: {e}")
            return False, f"Error: {str(e)}"
