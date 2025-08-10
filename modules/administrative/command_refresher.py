import discord
from discord.ext import commands
from modules.engine.lang_utils import load_language_pack, get_translation
import os
from typing import Dict

async def setup_command_refresher(bot: commands.Bot, config: Dict, language_pack: Dict):
    @commands.has_permissions(administrator=True)  # Only for discord server administrators
    @bot.tree.command(name="sync_commands", description="Synchronizuje komendy bota (tylko dla adminów).")
    async def sync_commands(interaction: discord.Interaction):
        "syncing bot commands after changes"
        await interaction.response.defer()

        if not language_pack:
            await interaction.followup.send("Failed to load language pack", ephemeral=True)
            return
    
        try:
            guild_id = int(os.getenv('GUILD_ID'))
            guild = discord.Object(id=guild_id)
            synced = await bot.tree.sync(guild=guild)
            await interaction.followup.send(get_translation("success_commands_synced_guild", language_pack, module="administrative", submodule="command_refresher", num_commands=len(synced), guild_id = guild_id))
        except Exception as e:
            await interaction.followup.send(
                get_translation("error_sync_commands", language_pack, module="general_errors", error=str(e)),
                ephemeral=True
            )
             