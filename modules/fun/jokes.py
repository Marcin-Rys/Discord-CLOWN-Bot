import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os
from typing import List
    
class Jokes(commands.Cog):
    #adding for module an name and description
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        #creating blank lists and dictionaires which will be populated.
        self.all_jokes: List[str] = []
        self.jokes_by_category: dict[str, List[str]] = {}
        self._load_jokes_from_file()

    def _load_jokes_from_file(self):
        """
        section to load jokes from json only once while initializing module
        """
        config = self.bot.config
        jokes_filename = config["module_files"]["jokes_file"]
        data_dir = config["directories"]["data_dir"]
        file_path = os.path.join(data_dir, jokes_filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
            # manipulating data and saving in attribute 'self'
            for category in data['joke_categories']:
                    category_name = category['category_name']
                    jokes_in_category = category['jokes']

                    self.all_jokes.extend(jokes_in_category)
                    self.jokes_by_category[category_name] = jokes_in_category

            print(f"Loaded succesfully {len(self.all_jokes)} jokes from {len(self.jokes_by_category)} categories") #TODO dodać tłumaczenie paczkę jezykową

        except FileNotFoundError:
            print (f"ERROR: Jokes file not found: {file_path}") #TODO dodać tłumaczenie paczkę jezykową
        except (json.JSONDecodeError, KeyError) as e:
            print(f"ERROR: Jokes file is damaged or has wrong format {e}") #TODO dodać tłumaczenie paczkę jezykową
        
    joke_group = app_commands.Group(name="kawal", description="Komendy do opowiadania kawałów") #TODO dodać tłumaczenie paczkę jezykową

    @joke_group.command(name="random", description="Tells random joke from random category") #TODO dodać tłumaczenie paczkę jezykową
    async def random_joke(self, interaction: discord.Interaction):
        if not self.all_jokes:
            await interaction.response.send_message("Sorry, I did not have any loaded jokes", ephemeral=True) #TODO dodać tłumaczenie paczkę jezykową
            return
        joke = random.choice(self.all_jokes)
        await interaction.response.send_message(joke)

    @joke_group.command(name="kategoria", description="Tells a random joke from category") #TODO dodać tłumaczenie paczkę jezykową
    @app_commands.describe(category="Select category from which you want to get a joke") #TODO dodać tłumaczenie paczkę jezykową
    async def category_joke(self, interaction: discord.Interaction, category: str):
        if category in self.jokes_by_category:
              joke = random.choice(self.jokes_by_category[category])
              await interaction.response.send_message(joke)
        else:
            await interaction.response.send_message(f"I dont know category '{category}'. Please select one from list.", ephemeral=True) #TODO dodać tłumaczenie paczkę jezykową

    # Autocomplete
    @category_joke.autocomplete('category')
    async def category_atuocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """
        This function is invoked when user is starting typing in option 'category', addding dynamic suggestions
        """
        categories = self.jokes_by_category.keys()
        return [
              app_commands.Choice(name=category, value=category)
              for category in categories if current.lower() in category.lower()
        ][:25] #discord allows 25 suggestions

#standard function to add module to bot
async def setup(bot: commands.Bot):
     await bot.add_cog(Jokes(bot))