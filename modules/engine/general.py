import discord
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        ### This listener will run if bot is succesfully connected to discord and is ready to work
        print("-" * 40)
        print("--- general.py| OK | Bot is connected and ready to work!")
        for guild in self.bot.guilds: #1. Printing information about server/guilds connected:
            print(f"--- general.py | OK | Connected to discord guild, bot = {self.bot.user} name = {guild.name}, ID = {guild.id}")
        
        print("\n--- general.py| OK | Loaded app commands:")
        if self.bot.tree.get_commands():
            for command in self.bot.tree.get_commands():
                print(f" -/{command.name}")
        else:
            print("--- general.py| ERROR | Not loaded app commands.")
        
        print("-" * 40)

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))