import discord
from discord.ext import commands, tasks
import json
import random
import os

class StatusManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.all_statuses = [] # Initializing blank dictionary for statuses
        self._load_statuses_from_file() # Loading statuses only once

        interval = self.bot.config.get("bot_settings", {}).get("status_change_interval_seconds", 120) # Loading interval from config with default value just for backup
        self.change_status.change_interval(seconds=interval) # Changing interval of this loop for those from config
        if self.all_statuses:
            self.change_status.start()

    def _load_statuses_from_file(self):
        config = self.bot.config
        filename = config["module_files"]["statuses_file"]
        dir_path = config["directories"]["data_dir"]
        file_path = os.path.join(dir_path, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            for category in data['status_categories']:
                emojis = category["emojis"]
                for status in category['statuses']:
                    random_emoji = random.choice(emojis)
                    self.all_statuses.append((status, random_emoji))

            print(f"Loaded succesfully {len(self.all_statuses)} available statuses.")
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"ERROR: Couldnt load file with statuses {e}. Status loop will not be loaded")
            self.all_statuses=[] #stop loading if data is corrupted.    

    async def _set_random_status(self):
        ### This helper just sets up random status, used in start and loop.
        if not self.all_statuses:
            return # Do nothing if there is no statuses loaded
        
        status, emoji = random.choice(self.all_statuses)
        activity = discord.Activity(
            type=discord.ActivityType.custom,
            name="custom", # This trick is needed
            state=f"{emoji} {status}"
        )
        await self.bot.change_presence(status=discord.Status.idle, activity=activity)
        print(f"Status changed to: {emoji} {status}")

    @tasks.loop(seconds=120) # This value is default, will be overwritten in __init__
    async def change_status(self):
        try:
            await self._set_random_status() # Periodic loop to change status
        except Exception as e:
            print(f"Error while changing status: {e}")
    @change_status.before_loop
    async def before_change_status(self):
        await self.bot.wait_until_ready()
        print("StatusManager: Oczekiwanie na gotowość bota przed uruchomieniem pętli statusów...")
        
    def module_unload(self):
            self.change_status.cancel() # Stops loop while module is unloaded

async def setup(bot: commands.Bot):
    await bot.add_cog(StatusManager(bot))