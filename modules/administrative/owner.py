import discord
from discord.ext import commands
from discord import app_commands

class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sync", description="Synchronizuje komendy z Discordem (tylko właściciel).")
    @app_commands.describe(server="Server ID for sync(optional)")
    @commands.is_owner()
    async def slash_sync(self, interaction: discord.Interaction, server: str = None):
        await interaction.response.defer(ephemeral=True)
        
        # Synchronizacja globalna (zmiany mogą potrwać do godziny)
        if server:
            try:
                guild = discord.Object(id=int(server))
                synced = await self.bot.tree.sync(guild=guild)
                await interaction.followup.send(f"Succesfully synchronized {len(synced)} commands with server {server}.")
            except (ValueError, discord.HTTPException) as e:
                await interaction.followup.send(f"ERROR: Incorrect server ID or API error: {e}")
        else:
            synced = await self.bot.tree.sync()
            await interaction.followup.send(f"Succesfully synchronized {len(synced)} commands globally. Changes might take an hour.")

    @commands.command(name="sync")
    @commands.is_owner() # Gwarantuje, że tylko Ty możesz jej użyć
    async def prefix_sync(self, ctx: commands.Context, server_id: int = None):
        """
        !sync [server_ID] - to sync commands with discord and guild
        """
        if server_id:
            # Synchronizacja z jednym, konkretnym serwerem (natychmiastowa)
            guild = discord.Object(id=server_id)
            synced = await self.bot.tree.sync(guild=guild)
            await ctx.send(f"Succesfully synchronized {len(synced)} commands with {server_id}.")
            print(f"Synchronized {len(synced)} commands with {server_id}.")
        else: 
            # Synchronizacja globalna (może potrwać do godziny)
            synced = await self.bot.tree.sync()
            await ctx.send(f"Succesfully synchronized {len(synced)} commands globally, changes might take an hour.")
            print(f"Synchronized {len(synced)} commands globally.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))