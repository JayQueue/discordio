"""Gemini AI service for generating movie and TV show recommendations."""
import google.generativeai as genai
from config import Config

class GeminiService:
    """Service for generating AI-powered content recommendations."""
    
    def __init__(self):
        """Initialize the Gemini service."""
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        print("✅ Gemini AI service initialized")
    
    async def search_content(self, query: str, content_type: str = "movie") -> str:
        """Generate content recommendations based on a query."""
        try:
            # Language mapping for Gemini responses
            language_names = {
                "ENGLISH": "English",
                "DUTCH": "Dutch",
                "FRENCH": "French",
                "GERMAN": "German",
                "SPANISH": "Spanish"
            }
            response_language = language_names.get(Config.BOT_LANG, Config.BOT_LANG)

            media_type = "films" if content_type == "movie" else "TV series"
            year_label = "Year" if content_type == "movie" else "Years"

            prompt = f"""You are a {media_type} recommendation assistant. Respond in {response_language}.

The user is searching for: "{query}"

Provide 3-5 relevant {media_type} recommendations.

IMPORTANT: Format your response EXACTLY as follows:

1. Title ({year_label}) - Short one-sentence description.
2. Title ({year_label}) - Short one-sentence description.

For series, use year ranges like (2008-2013) or (2016-) for ongoing series.
Provide ONLY the numbered list, no extra text.
Remember: Respond in {response_language}."""

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            return f"❌ Error searching: {str(e)}"
