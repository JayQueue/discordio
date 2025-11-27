"""Watched items cog - Shows removed and flagged watched items from library."""
import discord
from discord import app_commands
from discord.ext import commands
import requests
from typing import Optional
from utils.language import t
from models.user_auth import UserAuthManager


class WatchedFilterModal(discord.ui.Modal, title="Filter Watched Items"):
    """Modal for filtering watched items by date range, type, and status."""

    content_type = discord.ui.TextInput(
        label="Content Type",
        placeholder="movies, series, or all (default: all)",
        required=False,
        max_length=10
    )

    removed_status = discord.ui.TextInput(
        label="Removed Status",
        placeholder="yes, no, or all (default: all)",
        required=False,
        max_length=3
    )

    watched_status = discord.ui.TextInput(
        label="Watched Status",
        placeholder="yes, no, or all (default: all)",
        required=False,
        max_length=3
    )

    date_start = discord.ui.TextInput(
        label="Start Date (YYYY-MM-DD)",
        placeholder="2024-01-01 (leave empty for no filter)",
        required=False,
        max_length=10
    )

    date_end = discord.ui.TextInput(
        label="End Date (YYYY-MM-DD)",
        placeholder="2024-12-31 (leave empty for no filter)",
        required=False,
        max_length=10
    )

    def __init__(self, cog, interaction):
        super().__init__()
        self.cog = cog
        self.original_interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        await interaction.response.defer(ephemeral=True)

        # Parse content type
        content_filter = None
        if self.content_type.value:
            ct = self.content_type.value.lower().strip()
            if ct in ['movie', 'movies', 'film', 'films']:
                content_filter = 'movie'
            elif ct in ['series', 'serie', 'tv', 'show', 'shows']:
                content_filter = 'series'

        # Parse removed status
        removed_filter = None  # None means 'all'
        if self.removed_status.value:
            rs = self.removed_status.value.lower().strip()
            if rs in ['yes', 'y', 'true', '1']:
                removed_filter = True
            elif rs in ['no', 'n', 'false', '0']:
                removed_filter = False
            # else: leave as None for 'all'

        # Parse watched status
        watched_filter = None  # None means 'all'
        if self.watched_status.value:
            ws = self.watched_status.value.lower().strip()
            if ws in ['yes', 'y', 'true', '1']:
                watched_filter = True
            elif ws in ['no', 'n', 'false', '0']:
                watched_filter = False
            # else: leave as None for 'all'

        # Parse dates
        start_date = self.date_start.value.strip() if self.date_start.value else None
        end_date = self.date_end.value.strip() if self.date_end.value else None

        # Validate date format
        if start_date and len(start_date) != 10:
            await interaction.followup.send("❌ Invalid start date format. Use YYYY-MM-DD", ephemeral=True)
            return
        if end_date and len(end_date) != 10:
            await interaction.followup.send("❌ Invalid end date format. Use YYYY-MM-DD", ephemeral=True)
            return

        # Call the watched command with filters
        await self.cog._execute_watched_command(
            interaction,
            content_filter,
            start_date,
            end_date,
            removed_filter,
            watched_filter
        )


class WatchedCog(commands.Cog):
    """Cog for viewing removed and watched library items."""

    def __init__(self, bot, auth_manager: UserAuthManager):
        self.bot = bot
        self.auth_manager = auth_manager

    @app_commands.command(name="watched", description="View watched/removed items from your library")
    @app_commands.describe(
        filter_type="Quick filter by content type",
        use_advanced="Set to true to use advanced filtering with date ranges"
    )
    @app_commands.choices(filter_type=[
        app_commands.Choice(name="All Items", value="all"),
        app_commands.Choice(name="Movies Only", value="movies"),
        app_commands.Choice(name="Series Only", value="series"),
    ])
    async def watched_command(
        self,
        interaction: discord.Interaction,
        filter_type: app_commands.Choice[str] = None,
        use_advanced: bool = False
    ):
        """Show removed and flagged watched items from library."""

        # Check auth first
        auth_key = self.auth_manager.get_auth_key(interaction.user.id)
        if not auth_key:
            await interaction.response.send_message(t('LIBRARY_NO_AUTH'), ephemeral=True)
            return

        # If advanced filtering requested, show modal
        if use_advanced:
            modal = WatchedFilterModal(self, interaction)
            await interaction.response.send_modal(modal)
            return

        # Otherwise use quick filter
        content_filter = None
        if filter_type:
            if filter_type.value == 'movies':
                content_filter = 'movie'
            elif filter_type.value == 'series':
                content_filter = 'series'

        await interaction.response.defer(ephemeral=True)
        await self._execute_watched_command(interaction, content_filter, None, None, None, None)

    async def _execute_watched_command(
        self,
        interaction: discord.Interaction,
        content_type: Optional[str],
        date_start: Optional[str],
        date_end: Optional[str],
        removed_filter: Optional[bool] = None,
        watched_filter: Optional[bool] = None
    ):
        """Execute the watched command with given filters."""

        # Get user's auth key
        auth_key = self.auth_manager.get_auth_key(interaction.user.id)
        if not auth_key:
            await interaction.followup.send(t('LIBRARY_NO_AUTH'), ephemeral=True)
            return

        # Fetch library
        library = await self._fetch_library(auth_key)
        if not library:
            await interaction.followup.send("No library items found.", ephemeral=True)
            return

        # Filter items based on status filters
        filtered_items = []
        for item in library:
            removed = item.get("removed", False)
            state = item.get("state", {})
            flagged = state.get("flaggedWatched", 0)

            # Apply removed status filter
            if removed_filter is not None:
                if removed != removed_filter:
                    continue

            # Apply watched status filter
            if watched_filter is not None:
                is_watched = (flagged == 1)
                if is_watched != watched_filter:
                    continue

            # If no specific filters, default to showing removed OR watched items
            if removed_filter is None and watched_filter is None:
                if not (removed or flagged == 1):
                    continue

            item_type = item.get("type", "unknown")
            last_watched = state.get("lastWatched", "")

            # Only include movies and series, exclude channels and other types
            if item_type not in ['movie', 'series']:
                continue

            # Apply content type filter
            if content_type and item_type != content_type:
                continue

            # Apply date range filter
            if date_start and date_end and last_watched:
                # Extract date from ISO timestamp (YYYY-MM-DD)
                watched_date = last_watched[:10] if len(last_watched) >= 10 else ""
                if watched_date < date_start or watched_date > date_end:
                    continue

            filtered_items.append({
                "name": item.get("name", "Unknown"),
                "type": item_type,
                "removed": removed,
                "flagged": flagged,
                "last_watched": last_watched,
                "times_watched": state.get("timesWatched", 0),
                "time_offset": state.get("timeOffset", 0),
            })

        if not filtered_items:
            filter_desc = ""
            if content_type:
                filter_desc = f" {content_type}s"
            if removed_filter is not None:
                filter_desc += f" (removed: {'yes' if removed_filter else 'no'})"
            if watched_filter is not None:
                filter_desc += f" (watched: {'yes' if watched_filter else 'no'})"
            if date_start and date_end:
                filter_desc += f" between {date_start} and {date_end}"
            await interaction.followup.send(
                f"No items found{filter_desc}.",
                ephemeral=True
            )
            return

        # Limit to 25 items
        filtered_items = filtered_items[:25]

        # Show in table view
        await self._show_table_view(interaction, filtered_items, content_type, date_start, date_end)

    async def _fetch_library(self, auth_key: str) -> list:
        """Fetch library items from Stremio API."""
        api_url = "https://api.strem.io/api/datastoreGet"
        payload = {
            "authKey": auth_key,
            "collection": "libraryItem",
            "all": True
        }

        try:
            response = requests.post(api_url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch library. HTTP status: {response.status_code}")
                return []

            data = response.json()
            return data.get("result", [])
        except Exception as e:
            print(f"Error fetching library: {e}")
            return []

    async def _show_table_view(self, interaction, items, content_type=None, date_start=None, date_end=None):
        """Display items in table format."""
        embeds = []
        items_per_page = 10

        # Build title and description based on filters
        title_parts = []
        if content_type:
            title_parts.append(content_type.title() + "s")
        else:
            title_parts.append("All Items")

        title = f"🎬 Watched & Removed {' '.join(title_parts)}"

        description = "Items that are removed or flagged as watched"
        if date_start and date_end:
            description += f"\n📅 Date range: {date_start} to {date_end}"

        for page_num in range(0, len(items), items_per_page):
            page_items = items[page_num:page_num + items_per_page]

            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.purple()
            )

            for item in page_items:
                name = item['name'][:40]  # Truncate long names
                item_type = item['type']
                removed = "✓" if item['removed'] else "✗"
                flagged = "✓" if item['flagged'] == 1 else "✗"
                times = item['times_watched']

                type_emoji = "🎬" if item_type == "movie" else "📺"

                field_value = (
                    f"{type_emoji} **Type:** {item_type.title()}\n"
                    f"🗑️ **Removed:** {removed} | ⭐ **Watched:** {flagged}\n"
                    f"👁️ **Times watched:** {times}\n"
                    f"🕒 **Last watched:** {item['last_watched'][:10] if len(item['last_watched']) > 10 else item['last_watched']}"
                )

                embed.add_field(name=name, value=field_value, inline=False)

            embed.set_footer(text=f"Total items: {len(items)} • Page {len(embeds) + 1}/{(len(items) + items_per_page - 1) // items_per_page}")
            embeds.append(embed)

        if embeds:
            # Create simple pagination view
            view = WatchedPaginationView(embeds)
            await interaction.followup.send(embed=embeds[0], view=view, ephemeral=True)


class WatchedPaginationView(discord.ui.View):
    """Simple pagination for watched items."""

    def __init__(self, embeds: list):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.current_page = 0

        # Create navigation buttons
        self.prev_btn = discord.ui.Button(
            label=t('BUTTON_PREVIOUS'),
            style=discord.ButtonStyle.secondary,
            custom_id="prev",
            disabled=True
        )
        self.prev_btn.callback = self._previous_callback
        self.add_item(self.prev_btn)

        self.next_btn = discord.ui.Button(
            label=t('BUTTON_NEXT'),
            style=discord.ButtonStyle.secondary,
            custom_id="next",
            disabled=(len(embeds) <= 1)
        )
        self.next_btn.callback = self._next_callback
        self.add_item(self.next_btn)

    def _update_buttons(self) -> None:
        self.prev_btn.disabled = (self.current_page == 0)
        self.next_btn.disabled = (self.current_page >= len(self.embeds) - 1)

    async def _previous_callback(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.defer()

    async def _next_callback(self, interaction: discord.Interaction):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.defer()


async def setup(bot, auth_manager: UserAuthManager):
    """Setup function for the watched cog."""
    await bot.add_cog(WatchedCog(bot, auth_manager))
