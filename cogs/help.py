"""Help command cog."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.language import t

class HelpCog(commands.Cog):
    """Help and information commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all available commands and their usage")
    async def help_command(self, interaction: discord.Interaction):
        """Show help message with all available commands."""

        embed = discord.Embed(
            title=t('HELP_TITLE'),
            description=t('HELP_DESCRIPTION'),
            color=discord.Color.blue()
        )

        # Public commands
        embed.add_field(
            name=t('HELP_SEARCH_TITLE'),
            value=t('HELP_SEARCH_VALUE'),
            inline=False
        )

        embed.add_field(
            name=t('HELP_LIBRARY_TITLE'),
            value=t('HELP_LIBRARY_VALUE'),
            inline=False
        )

        embed.add_field(
            name=t('HELP_WATCHED_TITLE'),
            value=t('HELP_WATCHED_VALUE'),
            inline=False
        )

        embed.add_field(
            name=t('HELP_AUTH_TITLE'),
            value=t('HELP_AUTH_VALUE'),
            inline=False
        )

        embed.add_field(
            name=t('HELP_SYSTEM_TITLE'),
            value=t('HELP_SYSTEM_VALUE'),
            inline=False
        )

        # Admin commands
        if interaction.user.id == self.bot.owner_id:
            embed.add_field(
                name=t('HELP_ADMIN_TITLE'),
                value=t('HELP_ADMIN_VALUE'),
                inline=False
            )

        embed.set_footer(text=t('HELP_FOOTER'))

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    """Setup function to load this cog."""
    await bot.add_cog(HelpCog(bot))
