import discord
from discord.ext import commands
import json
import random
import os

class QuestionResponder(commands.Cog):
    def __init__(self,bot: commands.Bot):
        self.bot = bot
        self.all_answers = [] # Initializing without an list which will be populated with all responses
        self._load_answers_from_file() # Loading answers only once, during initialization

    def _load_answers_from_file(self):
        # Loads and flattens all responses from categorized JSON file
        config = self.bot.config
        filename = config["module_files"]["ama_file"]
        dir_path = config["directories"]["data_dir"]
        file_path = os.path.join(dir_path, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            for category in data['answer_categories']:  # Iterating through each category and adds responses to one large lists
                 self.all_answers.extend(category['answers'])

            print(f"Loaded succesfully {len(self.all_answers)} ama responses.")
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"ERROR!: Could not load ama response file: {e}")


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return # Ignore bot messages
        
        ## We are checking two statements:
        ## 1. If bot has been mentioned in message?
        ## 2. Does message ends with an question mark?(after removing white types from end)

        mentioned_ids = [user.id for user in message.mentions]
        is_bot_mentioned = self.bot.user.id in mentioned_ids
        is_a_question = message.content.strip().endswith('?')

        if is_a_question:
            print(f"--- DEBUG (Pytanie): Wiadomość to pytanie. Czy bot wspomniany? {is_bot_mentioned} ---")
        if is_bot_mentioned and is_a_question:
            if not self.all_answers: # Check if we have any response to randomize
                await message.reply("Nie umiem odpowiedzieć teraz na to pytanie, ŻEGNAM") #TODO language pack
                return
            
            response = random.choice(self.all_answers) # Select random response

            await message.reply(response) #Sends an response, better than "channel send" as it has bond with message


async def setup(bot: commands.Bot): #standard setup function
    await bot.add_cog(QuestionResponder(bot))