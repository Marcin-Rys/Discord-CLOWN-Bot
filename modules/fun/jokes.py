import discord
from discord.ext import commands
from discord import app_commands
import random
import aiosqlite
from typing import List, Optional

from ..engine.guild_utils import get_accessible_guilds_for_feature

class Jokes(commands.Cog):
    #adding for module an name and description
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = self.bot.config["database_path"]

    # --- Helper functions and for autocompletion
    async def get_categories_for_context(self, interaction: discord.Interaction) -> List[str]:
        """Gets available categories of jokes with context(server or DM)"""
        guilds_to_check = []
        if interaction.guild:
            guilds_to_check.append(interaction.guild)
        else:
            guilds_to_check = await get_accessible_guilds_for_feature(self.bot, interaction.user, "jokes_command")

        if not guilds_to_check:
            return[]
        
        guild_ids = [g.id for g in guilds_to_check]
        placeholders = ', '.join('?' for _ in guild_ids)

        categories = []
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                f"SELECT DISTINCT category FROM jokes WHERE guild_id IN ({placeholders})",
                guild_ids
            )
            rows = await cursor.fetchall()
            categories = [row[0] for row in rows]
        return categories
    
    async def category_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Dynamic autocompletion of jokes category"""
        categories = await self.get_categories_for_context(interaction)
        return [
            app_commands.Choice(name=category, value=category)
            for category in categories if current.lower() in category.lower()
        ][:25]
    

    # --- Command group ---
    joke_group = app_commands.Group(name="joke", description="Tells a joke from database")

    @joke_group.command(name="random", description="Tells random joke from all jokes")
    async def random_joke(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        guilds_to_check = []
        if interaction.guild:
            guilds_to_check.append(interaction.guild)
        else:
            guilds_to_check = await get_accessible_guilds_for_feature(self.bot, interaction.user, "jokes_command")
        
        if not guilds_to_check:
            await interaction.followup.send("Cannot find any jokes for you!", ephemeral=True)
            return
        
        guild_ids = [g.id for g in guilds_to_check]
        placeholders = ', '.join('?' for _ in guild_ids)

        joke_text = None
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                f"SELECT text FROM jokes WHERE guild_id IN ({placeholders}) ORDER BY RANDOM() LIMIT 1",
                guild_ids
            )
            result = await cursor.fetchone()
            if result:
                joke_text = result[0]

        if joke_text:
            await interaction.followup.send(joke_text)
        else: 
            await interaction.followup.send("Seems like there is no jokes for you", ephemeral=True)
            
    @joke_group.command(name="category", description="Tells random joke from selected category.")
    @app_commands.describe(category="Select category from which you want to roll a joke.")
    @app_commands.autocomplete(category=category_autocomplete)
    async def category_joke(self, interaction: discord.Interaction, category: str):
        await interaction.response.defer(thinking=True)

        guilds_to_check = []
        if interaction.guild:
            guilds_to_check.append(interaction.guild)
        else:
            guilds_to_check = await get_accessible_guilds_for_feature(self.bot, interaction.user, "jokes_command")

        if not guilds_to_check:
            await interaction.followup.send("Cannot find any jokes for you!", ephemeral=True)
            return
        
        guild_ids = [g.id for g in guilds_to_check]
        placeholders = ', '.join('?' for _ in guild_ids)
        params = guild_ids + [category]

        joke_text = None
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute (
                f"SELECT text FROM jokes WHERE guild_id IN ({placeholders}) AND category = ? ORDER BY RANDOM() LIMIT 1",
                params
            )
            result = await cursor.fetchone()
            if result:
                joke_text = result[0]

        if joke_text:
            await interaction.followup.send(joke_text)
        else:
            await interaction.followup.send(f"Couldn't find any jokes in category '{category}' that are available for you", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Jokes(bot))