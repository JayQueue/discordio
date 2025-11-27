"""Stremio Discord Bot - Main Entry Point"""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import sys
import traceback
from config import Config
from models.user_auth import UserAuthManager
from models.user_history import UserHistoryManager
from utils.language import Language, t

class StremioBot(commands.Bot):
    def __init__(self):
        print(t('INIT_BOT'))
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True  # Required for DM functionality and guild member access
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.auth_manager = UserAuthManager()
        self.history_manager = UserHistoryManager()
        self.synced = False  # Track if commands have been synced
        print(t('INIT_SUCCESS'))

    async def setup_hook(self):
        """Setup hook for loading cogs and setting up error handlers"""
        # Set up global error handler for slash commands
        async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            if isinstance(error, app_commands.CommandOnCooldown):
                await interaction.response.send_message(
                    f"⏱️ This command is on cooldown. Try again in {error.retry_after:.2f}s",
                    ephemeral=True
                )
            elif isinstance(error, app_commands.MissingPermissions):
                await interaction.response.send_message(
                    "❌ You don't have permission to use this command.",
                    ephemeral=True
                )
            elif isinstance(error, app_commands.CheckFailure):
                await interaction.response.send_message(
                    "❌ You can't use this command here.",
                    ephemeral=True
                )
            else:
                print(f"❌ App command error: {error}")
                traceback.print_exception(type(error), error, error.__traceback__)
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        t('ERROR_COMMAND_FAILED'),
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        t('ERROR_COMMAND_FAILED'),
                        ephemeral=True
                    )

        self.tree.on_error = on_app_command_error

        # Load cogs
        print(t('LOADING_COGS'))
        try:
            from cogs import search, library, admin, help as help_cog, watched

            print(t('LOADING_SEARCH_COG'))
            await search.setup(self, self.auth_manager, self.history_manager)
            print(t('COG_LOADED', cog='Search'))

            print(t('LOADING_LIBRARY_COG'))
            await library.setup(self, self.auth_manager)
            print(t('COG_LOADED', cog='Library'))

            print(t('LOADING_ADMIN_COG'))
            await admin.setup(self)
            print(t('COG_LOADED', cog='Admin'))

            print(t('LOADING_HELP_COG'))
            await help_cog.setup(self)
            print(t('COG_LOADED', cog='Help'))

            print("Loading Watched cog...")
            await watched.setup(self, self.auth_manager)
            print(t('COG_LOADED', cog='Watched'))

            print(t('ALL_COGS_LOADED'))
        except Exception as e:
            print(t('FAILED_LOAD_COGS', error=e))
            traceback.print_exc()
            sys.exit(1)

    async def on_ready(self):
        print("=" * 50)
        print(t('BOT_READY'))
        print(t('LOGGED_IN_AS', name=self.user.name))
        print(t('BOT_ID', id=self.user.id))
        print(t('CONNECTED_TO_SERVERS', count=len(self.guilds)))
        print("=" * 50)

        # Set owner ID from config for help command
        if Config.ADMIN_USER_ID:
            self.owner_id = Config.ADMIN_USER_ID

        # Sync slash commands (only once)
        if not self.synced:
            print("🔄 Syncing slash commands...")
            try:
                synced = await self.tree.sync()
                self.synced = True
                print(f"✅ Synced {len(synced)} slash command(s)")
            except Exception as e:
                print(f"❌ Failed to sync commands: {e}")
                traceback.print_exc()

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=t('BOT_PRESENCE')
            )
        )

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(t('ERROR_COMMAND_NOT_FOUND'))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(t('ERROR_MISSING_ARGUMENT', param=error.param.name))
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(t('ERROR_DM_ONLY'))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(t('ERROR_NO_DM'))
        else:
            print(f"❌ Command error: {error}")
            traceback.print_exception(type(error), error, error.__traceback__)
            await ctx.send(t('ERROR_COMMAND_FAILED'))

    async def close(self):
        print(t('SHUTTING_DOWN'))
        # SQLite auto-commits, no need to manually save
        await super().close()
        print(t('SHUTDOWN_COMPLETE'))

async def main():
    print(t('STARTING_BOT'))
    print()

    try:
        print(t('LOADING_CONFIG'))
        Config.load()
        # Load language after config is loaded
        Language.load(Config.BOT_LANG)
        Config.print_debug_info()
        print()
    except ValueError as e:
        print(t('CONFIG_ERROR', error=e))
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(t('CREATING_BOT'))
    bot = StremioBot()

    print(t('CONNECTING_DISCORD'))
    try:
        async with bot:
            await bot.start(Config.BOT_TOKEN)
    except discord.LoginFailure:
        print(t('INVALID_TOKEN'))
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{t('INTERRUPTED')}")
    except Exception as e:
        print(t('FATAL_ERROR', error=e))
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Load a temporary language for the initial messages
    # This will be reloaded in main() with the config value
    try:
        Language.load("ENGLISH")
    except:
        pass  # If language file doesn't exist yet, continue anyway

    print("=" * 50)
    print("STREMIO DISCORD BOT - STARTING")
    print("=" * 50)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        try:
            print(f"\n{t('BOT_STOPPED')}")
        except:
            print("\n👋 Bot stopped by user")
    except Exception as e:
        try:
            print(t('UNEXPECTED_ERROR', error=e))
        except:
            print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
