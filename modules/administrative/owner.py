import discord
from discord.ext import commands
from discord import app_commands

class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sync", description="Synchronizuje komendy z Discordem (tylko właściciel).")
    @commands.is_owner()
    async def sync(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Synchronizacja globalna (zmiany mogą potrwać do godziny)
        synced = await self.bot.tree.sync()
        print(f"Zsynchronizowano {len(synced)} komend globalnie.")
        await interaction.followup.send(f"Zsynchronizowano {len(synced)} komend globalnie.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))