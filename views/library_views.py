"""Discord UI components for library browsing."""
import discord
from services.tmdb import TMDBService
from services.stremio import StremioService
from utils.language import t

class ItemActionsView(discord.ui.View):
    """View for choosing actions on a library item (Share or Remove)."""

    def __init__(self, item: dict, bot, interaction: discord.Interaction, auth_key: str):
        super().__init__(timeout=180)
        self.item = item
        self.bot = bot
        self.guild = interaction.guild
        self.auth_key = auth_key

        # Share button
        self.share_btn = discord.ui.Button(
            label="📤 Share",
            style=discord.ButtonStyle.primary
        )
        self.share_btn.callback = self._share_callback
        self.add_item(self.share_btn)

        # Remove button
        self.remove_btn = discord.ui.Button(
            label="🗑️ Remove",
            style=discord.ButtonStyle.danger
        )
        self.remove_btn.callback = self._remove_callback
        self.add_item(self.remove_btn)

        # Cancel button
        self.cancel_btn = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary
        )
        self.cancel_btn.callback = self._cancel_callback
        self.add_item(self.cancel_btn)

    async def _share_callback(self, interaction: discord.Interaction):
        """Open share menu."""
        share_view = ShareItemView(self.item, self.bot, interaction)
        await interaction.response.send_message(
            f"**Share:** {self.item.get('name', 'Unknown')}\nChoose where to share:",
            view=share_view,
            ephemeral=True
        )
        self.stop()

    async def _remove_callback(self, interaction: discord.Interaction):
        """Remove item from library."""
        item_id = self.item.get('_id')
        item_type = self.item.get('type')
        item_name = self.item.get('name', 'Unknown')

        success, message = StremioService.remove_from_library(
            self.auth_key,
            item_id,
            item_type,
            item_name
        )

        if success:
            await interaction.response.send_message(
                f"✅ Removed **{item_name}** from your library!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Failed to remove: {message}",
                ephemeral=True
            )
        self.stop()

    async def _cancel_callback(self, interaction: discord.Interaction):
        """Cancel action."""
        await interaction.response.send_message("Cancelled", ephemeral=True)
        self.stop()


class ShareItemView(discord.ui.View):
    """View for sharing a library item to channel or DM."""

    def __init__(self, item: dict, bot, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.item = item
        self.bot = bot
        self.guild = interaction.guild
        self.selected_channel = None
        self.selected_user = None

        # Add channel selector
        channel_options = []
        if self.guild:
            for channel in self.guild.text_channels:
                # Only add channels where the user has permission to view
                if channel.permissions_for(interaction.user).send_messages:
                    channel_options.append(
                        discord.SelectOption(
                            label=f"#{channel.name}",
                            value=str(channel.id),
                            description=f"Share to #{channel.name}"
                        )
                    )

        if channel_options:
            self.channel_select = discord.ui.Select(
                placeholder="Select a channel to share to...",
                options=channel_options[:25],  # Discord limit
                custom_id="channel_select"
            )
            self.channel_select.callback = self._channel_select_callback
            self.add_item(self.channel_select)

        # Add user selector
        user_options = []
        if self.guild:
            for member in self.guild.members:
                # Don't include bots or the user themselves
                if not member.bot and member.id != interaction.user.id:
                    user_options.append(
                        discord.SelectOption(
                            label=member.display_name,
                            value=str(member.id),
                            description=f"DM {member.display_name}"
                        )
                    )

        if user_options:
            self.user_select = discord.ui.Select(
                placeholder="Or select a user to DM...",
                options=user_options[:25],  # Discord limit
                custom_id="user_select"
            )
            self.user_select.callback = self._user_select_callback
            self.add_item(self.user_select)

        # Add share button
        self.share_btn = discord.ui.Button(
            label="📤 Share",
            style=discord.ButtonStyle.primary,
            custom_id="share",
            disabled=True
        )
        self.share_btn.callback = self._share_callback
        self.add_item(self.share_btn)

        # Add cancel button
        self.cancel_btn = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            custom_id="cancel"
        )
        self.cancel_btn.callback = self._cancel_callback
        self.add_item(self.cancel_btn)

    async def _channel_select_callback(self, interaction: discord.Interaction):
        """Handle channel selection."""
        self.selected_channel = int(self.channel_select.values[0])
        self.selected_user = None
        self.share_btn.disabled = False
        await interaction.response.edit_message(view=self)

    async def _user_select_callback(self, interaction: discord.Interaction):
        """Handle user selection."""
        self.selected_user = int(self.user_select.values[0])
        self.selected_channel = None
        self.share_btn.disabled = False
        await interaction.response.edit_message(view=self)

    async def _share_callback(self, interaction: discord.Interaction):
        """Share item to selected channel or user."""
        name = self.item.get('name', 'Unknown')
        item_type = self.item.get('type', 'unknown')
        item_id = self.item.get('_id', 'no-id')
        year = self.item.get('year', '')
        state = self.item.get('state', {})
        watched = t('STATUS_WATCHED') if state.get('flaggedWatched') else t('STATUS_NOT_WATCHED')
        type_emoji = t('TYPE_MOVIE') if item_type == "movie" else t('TYPE_SERIES')

        # Create public embed
        color = discord.Color.green() if state.get('flaggedWatched') else discord.Color.blue()
        embed = discord.Embed(
            title=f"{type_emoji} {name}" + (f" ({year})" if year else ""),
            description=f"{t('ITEM_TYPE', type=item_type.title())}\n{t('ITEM_STATUS', status=watched)}\n{t('ITEM_ID', id=item_id)}",
            color=color
        )

        poster_url = TMDBService.get_poster(item_id)
        if poster_url:
            embed.set_thumbnail(url=poster_url)

        embed.set_footer(text=f"Shared by {interaction.user.display_name}")

        try:
            if self.selected_channel:
                # Share to channel
                channel = self.guild.get_channel(self.selected_channel)
                if channel:
                    await channel.send(embed=embed)
                    await interaction.response.send_message(f"✅ Shared to #{channel.name}!", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Channel not found!", ephemeral=True)
            elif self.selected_user:
                # Share to user DM
                user = self.guild.get_member(self.selected_user)
                if user:
                    await user.send(embed=embed)
                    await interaction.response.send_message(f"✅ Sent DM to {user.display_name}!", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ User not found!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ No permission to send message!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error sharing: {e}", ephemeral=True)

        self.stop()

    async def _cancel_callback(self, interaction: discord.Interaction):
        """Cancel sharing."""
        await interaction.response.send_message("Cancelled", ephemeral=True)
        self.stop()


class LibraryPaginationView(discord.ui.View):
    """Pagination controls for browsing library items with action buttons."""

    def __init__(self, embeds: list, items: list, bot, auth_key: str, is_table: bool = False, items_per_page: int = 1):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.items = items
        self.bot = bot
        self.auth_key = auth_key
        self.current_page = 0
        self.is_table = is_table
        self.items_per_page = items_per_page
        self.action_buttons = []

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

        # Add initial action buttons
        self._update_action_buttons()

    def _update_action_buttons(self) -> None:
        """Update action buttons for items on current page."""
        # Remove existing action buttons
        for btn in self.action_buttons:
            self.remove_item(btn)
        self.action_buttons.clear()

        if self.is_table:
            # For table view, add an action button for each item on the page
            start_idx = self.current_page * self.items_per_page
            end_idx = min(start_idx + self.items_per_page, len(self.items))
            page_items = self.items[start_idx:end_idx]

            for i, item in enumerate(page_items):
                item_name = item.get('name', 'Unknown')
                # Truncate name if too long
                if len(item_name) > 15:
                    item_name = item_name[:12] + "..."

                btn = discord.ui.Button(
                    label=f"⚙️ {item_name}",
                    style=discord.ButtonStyle.primary,
                    custom_id=f"action_{start_idx + i}"
                )
                # Create a closure to capture the item index
                def make_callback(item_idx):
                    async def callback(interaction: discord.Interaction):
                        await self._action_callback(interaction, item_idx)
                    return callback

                btn.callback = make_callback(start_idx + i)
                self.add_item(btn)
                self.action_buttons.append(btn)
        else:
            # For grid view, add single action button for current item
            btn = discord.ui.Button(
                label="⚙️ Actions",
                style=discord.ButtonStyle.primary,
                custom_id="actions"
            )
            btn.callback = lambda interaction: self._action_callback(interaction, self.current_page)
            self.add_item(btn)
            self.action_buttons.append(btn)

    def _update_buttons(self) -> None:
        self.prev_btn.disabled = (self.current_page == 0)
        self.next_btn.disabled = (self.current_page >= len(self.embeds) - 1)
        self._update_action_buttons()

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

    async def _action_callback(self, interaction: discord.Interaction, item_idx: int):
        """Handle actions on a specific item (Share or Remove)."""
        current_item = self.items[item_idx]

        # Create actions view
        actions_view = ItemActionsView(current_item, self.bot, interaction, self.auth_key)

        # Send ephemeral message with action options
        await interaction.response.send_message(
            f"**{current_item.get('name', 'Unknown')}**\nChoose an action:",
            view=actions_view,
            ephemeral=True
        )
