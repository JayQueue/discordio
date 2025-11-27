"""Library commands cog."""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal
from services.stremio import StremioService
from services.tmdb import TMDBService
from models.user_auth import UserAuthManager
from views.library_views import LibraryPaginationView, ShareItemView
from utils.language import t

class LibraryCog(commands.Cog):
    def __init__(self, bot, auth_manager):
        self.bot = bot
        self.auth_manager = auth_manager

    @app_commands.command(name="library", description="View your Stremio library")
    @app_commands.describe(filter="Filter library by type or view mode")
    @app_commands.choices(filter=[
        app_commands.Choice(name="All (Grid with Posters)", value="all"),
        app_commands.Choice(name="All (List)", value="list"),
        app_commands.Choice(name="Movies Only", value="movies"),
        app_commands.Choice(name="Series Only", value="series"),
    ])
    async def library_command(
        self,
        interaction: discord.Interaction,
        filter: app_commands.Choice[str] = None
    ):
        """Show library with optional filtering."""
        auth_key = self.auth_manager.get_auth_key(interaction.user.id)

        if not auth_key:
            await interaction.response.send_message(t('LIBRARY_NO_AUTH'), ephemeral=True)
            return

        # Defer response as this might take a moment
        await interaction.response.defer(ephemeral=True)

        active_items = StremioService.get_active_items(auth_key)

        if not active_items:
            await interaction.followup.send(t('LIBRARY_EMPTY'), ephemeral=True)
            return

        # Get filter value
        filter_value = filter.value if filter else "all"

        # Filter items based on type
        if filter_value == 'movies':
            filtered_items = [item for item in active_items if item.get('type') == 'movie']
            view_mode = 'table'
        elif filter_value == 'series':
            filtered_items = [item for item in active_items if item.get('type') == 'series']
            view_mode = 'table'
        elif filter_value == 'list':
            filtered_items = active_items
            view_mode = 'table'
        else:  # all
            filtered_items = active_items
            view_mode = 'grid'

        if not filtered_items:
            await interaction.followup.send(f"No {filter_value} found in your library!", ephemeral=True)
            return

        # Limit to 25 items
        filtered_items = filtered_items[:25]

        # Show appropriate view
        if view_mode == 'grid':
            await self._show_grid_view(interaction, filtered_items, auth_key)
        else:
            await self._show_table_view(interaction, filtered_items, filter_value, auth_key)

    async def _show_grid_view(self, interaction, items, auth_key):
        """Show grid view with posters and action buttons."""
        embeds = []

        for idx, item in enumerate(items):
            name = item.get('name', 'Unknown')
            item_type = item.get('type', 'unknown')
            item_id = item.get('_id', 'no-id')
            year = item.get('year', '')
            state = item.get('state', {})
            watched = t('STATUS_WATCHED') if state.get('flaggedWatched') else t('STATUS_NOT_WATCHED')
            type_emoji = t('TYPE_MOVIE') if item_type == "movie" else t('TYPE_SERIES')
            color = discord.Color.green() if state.get('flaggedWatched') else discord.Color.blue()

            description = t('ITEM_TYPE', type=item_type.title()) + "\n" + \
                         t('ITEM_STATUS', status=watched) + "\n" + \
                         t('ITEM_ID', id=item_id)

            embed = discord.Embed(
                title=f"{type_emoji} {name}" + (f" ({year})" if year else ""),
                description=description,
                color=color
            )

            poster_url = TMDBService.get_poster(item_id)
            if poster_url:
                embed.set_image(url=poster_url)

            embed.set_footer(text=t('LIBRARY_ITEM_OF', current=idx + 1, total=len(items)))
            embeds.append(embed)

        if embeds:
            view = LibraryPaginationView(embeds, items, self.bot, auth_key)
            await interaction.followup.send(embed=embeds[0], view=view, ephemeral=True)

    async def _show_table_view(self, interaction, items, filter_type, auth_key):
        """Show table view with action buttons for each item."""
        pages = []
        items_per_page = 5

        for page_num in range(0, len(items), items_per_page):
            page_items = items[page_num:page_num + items_per_page]

            type_name = filter_type.title() if filter_type != 'all' else 'Library'
            embed = discord.Embed(
                title=f"📚 {type_name}",
                description=t('LIBRARY_PAGE', page=page_num // items_per_page + 1),
                color=discord.Color.blue()
            )

            for item in page_items:
                name = item.get('name', 'Unknown')
                item_type = item.get('type', 'unknown')
                year = item.get('year', '')
                state = item.get('state', {})
                watched_emoji = "✅" if state.get('flaggedWatched') else "⏳"
                type_emoji = t('TYPE_MOVIE') if item_type == "movie" else t('TYPE_SERIES')

                field_value = f"{type_emoji} **{item_type.title()}**"
                if year:
                    field_value += f" • {year}"
                field_value += f"\n{watched_emoji}"

                embed.add_field(name=name, value=field_value, inline=False)

            embed.set_footer(text=t('LIBRARY_TOTAL_ITEMS', count=len(items)))
            pages.append(embed)

        if pages:
            view = LibraryPaginationView(pages, items, self.bot, auth_key, is_table=True, items_per_page=items_per_page)
            await interaction.followup.send(embed=pages[0], view=view, ephemeral=True)

    @app_commands.command(name="setauth", description="Set your Stremio auth key (DM only)")
    @app_commands.describe(auth_key="Your Stremio authentication key")
    async def setauth_command(self, interaction: discord.Interaction, auth_key: str):
        """Set Stremio auth key (DM only)."""
        # Check if command is in DM
        if interaction.guild is not None:
            await interaction.response.send_message(
                "❌ This command can only be used in DMs for security reasons.",
                ephemeral=True
            )
            return

        self.auth_manager.set_auth_key(interaction.user.id, auth_key)
        await interaction.response.send_message(t('SETAUTH_SUCCESS'), ephemeral=True)

    @app_commands.command(name="removeauth", description="Remove your Stremio auth key (DM only)")
    async def removeauth_command(self, interaction: discord.Interaction):
        """Remove Stremio auth key (DM only)."""
        # Check if command is in DM
        if interaction.guild is not None:
            await interaction.response.send_message(
                "❌ This command can only be used in DMs for security reasons.",
                ephemeral=True
            )
            return

        removed = self.auth_manager.remove_auth_key(interaction.user.id)
        if removed:
            await interaction.response.send_message(t('REMOVEAUTH_SUCCESS'), ephemeral=True)
        else:
            await interaction.response.send_message(t('REMOVEAUTH_NONE'), ephemeral=True)

    @app_commands.command(name="checkauth", description="Check if your auth key is set (DM only)")
    async def checkauth_command(self, interaction: discord.Interaction):
        """Check if auth key is set (DM only)."""
        # Check if command is in DM
        if interaction.guild is not None:
            await interaction.response.send_message(
                "❌ This command can only be used in DMs for security reasons.",
                ephemeral=True
            )
            return

        has_auth = self.auth_manager.get_auth_key(interaction.user.id) is not None
        if has_auth:
            await interaction.response.send_message("✅ Your auth key is set.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No auth key set. Use `/setauth` to set one.", ephemeral=True)

async def setup(bot, auth_manager):
    await bot.add_cog(LibraryCog(bot, auth_manager))
