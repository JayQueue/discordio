"""Search commands cog."""
import discord
from discord import app_commands
from discord.ext import commands
from services.gemini import GeminiService
from utils.parsers import RecommendationParser
from views.search_views import AddToLibraryView
from models.user_auth import UserAuthManager
from models.user_history import UserHistoryManager
from utils.language import t

class SearchCog(commands.Cog):
    def __init__(self, bot, auth_manager, history_manager):
        self.bot = bot
        self.auth_manager = auth_manager
        self.history_manager = history_manager
        self.gemini = GeminiService()

    @app_commands.command(name="film", description="Search for movie recommendations using AI")
    @app_commands.describe(query="Describe the type of movie you're looking for")
    async def film_command(self, interaction: discord.Interaction, query: str):
        """Search for movie recommendations."""
        await interaction.response.defer()

        result = await self.gemini.search_content(query, "movie")
        recommendations = RecommendationParser.parse_recommendations(result)

        if recommendations:
            view = AddToLibraryView(recommendations, "movie", self.auth_manager, self.history_manager, interaction.user.id)
            await interaction.followup.send(result + "\n\n" + t('CLICK_TO_ADD'), view=view)
        else:
            await interaction.followup.send(result)

    @app_commands.command(name="serie", description="Search for series recommendations using AI")
    @app_commands.describe(query="Describe the type of series you're looking for")
    async def serie_command(self, interaction: discord.Interaction, query: str):
        """Search for series recommendations."""
        await interaction.response.defer()

        result = await self.gemini.search_content(query, "series")
        recommendations = RecommendationParser.parse_recommendations(result)

        if recommendations:
            view = AddToLibraryView(recommendations, "series", self.auth_manager, self.history_manager, interaction.user.id)
            await interaction.followup.send(result + "\n\n" + t('CLICK_TO_ADD'), view=view)
        else:
            await interaction.followup.send(result)

async def setup(bot, auth_manager, history_manager):
    await bot.add_cog(SearchCog(bot, auth_manager, history_manager))
