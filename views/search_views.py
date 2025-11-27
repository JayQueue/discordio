"""Discord UI components for search functionality."""
import discord
from services.tmdb import TMDBService
from services.stremio import StremioService
from models.user_auth import UserAuthManager
from models.user_history import UserHistoryManager
from utils.language import t

class AddToLibraryView(discord.ui.View):
    """Interactive button view for adding search results to library."""

    def __init__(self, recommendations: list, content_type: str, auth_manager: UserAuthManager, history_manager: UserHistoryManager, user_id: int):
        super().__init__(timeout=180)
        self.recommendations = recommendations
        self.content_type = content_type
        self.auth_manager = auth_manager
        self.history_manager = history_manager
        self.user_id = user_id
        
        for idx, rec in enumerate(recommendations[:5]):
            button = discord.ui.Button(
                label=f"{idx + 1}. {rec['title'][:40]}",
                style=discord.ButtonStyle.primary,
                custom_id=f"add_{idx}"
            )
            button.callback = self._create_callback(idx)
            self.add_item(button)
    
    def _create_callback(self, index: int):
        async def button_callback(interaction: discord.Interaction):
            rec = self.recommendations[index]
            title = rec['title']

            await interaction.response.defer(ephemeral=True)

            auth_key = self.auth_manager.get_auth_key(interaction.user.id)

            if not auth_key:
                await interaction.followup.send(
                    t('ADD_NO_AUTH'),
                    ephemeral=True
                )
                return

            item_id = TMDBService.search_title(title, self.content_type)

            if item_id:
                success, message = StremioService.add_to_library(
                    auth_key, item_id, self.content_type, title
                )

                if success:
                    # Log user action for future recommendations
                    self.history_manager.log_library_addition(
                        self.user_id,
                        self.content_type,
                        item_id,
                        title
                    )

                    await interaction.followup.send(
                        t('ADD_SUCCESS', title=title, id=item_id),
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        t('ADD_FAILED', message=message),
                        ephemeral=True
                    )
            else:
                await interaction.followup.send(
                    t('ADD_NOT_FOUND', title=title),
                    ephemeral=True
                )

        return button_callback
