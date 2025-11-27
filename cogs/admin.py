"""Admin commands cog."""
import discord
from discord import app_commands
from discord.ext import commands
import docker
from config import Config
from utils.language import t

def is_admin():
    """Check if user is admin"""
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id == Config.ADMIN_USER_ID
    return app_commands.check(predicate)

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.docker_client = docker.from_env()
        except:
            self.docker_client = None

    @app_commands.command(name="ping", description="Test bot responsiveness (admin only)")
    @is_admin()
    async def ping_command(self, interaction: discord.Interaction):
        """Test bot responsiveness."""
        await interaction.response.send_message(t('ADMIN_PING_RESPONSE'), ephemeral=True)

    @app_commands.command(name="status", description="Check Docker container status")
    async def status_command(self, interaction: discord.Interaction):
        """Check status of monitored Docker containers."""
        # Check if monitoring is configured
        if not Config.MONITORED_CONTAINERS:
            await interaction.response.send_message(
                "⚙️ Container monitoring is not configured.\n"
                "Set `MONITORED_CONTAINERS` in your .env file to enable this feature.",
                ephemeral=True
            )
            return

        if not self.docker_client:
            await interaction.response.send_message(t('ADMIN_DOCKER_UNAVAILABLE'), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        containers = self.docker_client.containers.list(all=True)
        container_dict = {c.name: c for c in containers}

        # Check status of all monitored containers
        all_running = True
        failed_containers = []
        status_lines = []

        for name in Config.MONITORED_CONTAINERS:
            if name in container_dict:
                state = container_dict[name].status
                emoji = "✅" if state == "running" else "❌"
                status_lines.append(f"{emoji} **{name}**: {state}")

                if state != "running":
                    all_running = False
                    failed_containers.append(f"{name} ({state})")
            else:
                status_lines.append(f"❓ **{name}**: not found")
                all_running = False
                failed_containers.append(f"{name} (not found)")

        # Everyone sees simple status message
        if all_running:
            await interaction.followup.send(t('ADMIN_STATUS_ALL_OK'), ephemeral=True)
        else:
            # Show generic message to users
            await interaction.followup.send(t('ADMIN_STATUS_ISSUES'), ephemeral=True)

            # Send detailed status to admin via DM
            if Config.ADMIN_USER_ID:
                try:
                    admin_user = await self.bot.fetch_user(Config.ADMIN_USER_ID)
                    dm_message = "🚨 **Service Alert**\n\n" + t('ADMIN_STATUS_TITLE') + "\n" + "\n".join(status_lines)
                    await admin_user.send(dm_message)
                except Exception as e:
                    print(f"⚠️ Could not send DM to admin: {e}")

    @app_commands.command(name="restart", description="Restart a Docker container (admin only)")
    @app_commands.describe(container_name="Name of the container to restart")
    @is_admin()
    async def restart_command(self, interaction: discord.Interaction, container_name: str):
        """Restart a Docker container."""
        try:
            container = self.docker_client.containers.get(container_name)
            container.restart()
            await interaction.response.send_message(
                t('ADMIN_RESTART_SUCCESS', container=container_name),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                t('ADMIN_RESTART_ERROR', error=e),
                ephemeral=True
            )

    @app_commands.command(name="whoami", description="Show your user ID and admin status")
    async def whoami_command(self, interaction: discord.Interaction):
        """Show user ID and admin status."""
        is_admin_user = interaction.user.id == Config.ADMIN_USER_ID
        await interaction.response.send_message(
            t('ADMIN_WHOAMI_RESPONSE', user_id=interaction.user.id, is_admin=is_admin_user),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
