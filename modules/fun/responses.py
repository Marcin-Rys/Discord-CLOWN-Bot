import discord
from discord.ext import commands
import json
import os
from ..engine.cooldown_manager import CooldownManager

class MessageResponder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.responses = {} #initializing blank dictionary
        self._load_responses() #starting an method loading data only once, while Cog/module will initialize
        
        db_path = self.bot.config["database_path"]  # Assuming database path is set in config
        cooldown_configs = {}
        try:
            with open("config/cooldowns.json", 'r', encoding='utf-8') as f:
                cooldown_configs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Cannot (Sra module): cannot load cooldowns file: {e}")
        self.cooldown_manager = CooldownManager(db_path, cooldown_configs)

    def _load_responses(self):
        config = self.bot.config
        filename = config["module_files"]["responses_file"]
        dir_path = config["directories"]["data_dir"]
        file_path = os.path.join(dir_path, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.responses = {key.lower(): value for key, value in json.load(file).items()} #loading responses and we will change keys for small letters.
            print(f"Loaded succesfully {len(self.responses)} responses.")
        except FileNotFoundError:
            print(f"Error! Not found file with responses: {file_path}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error! File with responses is damaged or has wrong format!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot: #1. Ignore messages from Bot itself(or other bots)
            return 
        
        message_content_lower = message.content.lower() #2. Load message and change it to small letters

        if message_content_lower in self.responses: #3. Check if message is in our dictionary loaded into memory
            feature_name = f"{message_content_lower}_response"
            can_use,reason = await self.cooldown_manager.check_cooldown(message.author.id, message.guild.id, feature_name)
            if not can_use:
                await message.channel.send(f"Hola hola {message.author}, zwolnij z użyciem {feature_name}! {reason}")
                return
            await self.cooldown_manager.record_usage(message.author.id, message.guild.id, feature_name)
            response_text = self.responses[message_content_lower]
            await message.channel.send(response_text)
        await self.bot.process_commands(message) #4. Process commands after checking responses
        
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageResponder(bot))
