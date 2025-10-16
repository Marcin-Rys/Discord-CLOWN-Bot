import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
from typing import Optional, List, Dict
from ..engine.cooldown_manager import CooldownManager


class Swearer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.swears: List[str] = []
        self.punchlines: List[str] = [] # Loading blank dictionaries
        self._load_data() # Loading data once during Cog/Module startup
        
        db_path = self.bot.config["database_path"]  # Assuming database path is set in config
        self.cooldown_manager = CooldownManager(db_path)

    def _load_data(self):
        # Private method to load swears and puents from JSON file.
        config = self.bot.config
        try: 
            filename = config["data_files"]["swears_file"]
            dir_path = config["data_dir"]
            file_path = os.path.join(dir_path, filename)

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Saving data to 'self' attributes for stable access
            self.swears = data.get("swears", [])
            self.punchlines = data.get("punchlines", [])

            print(f"Loaded succesfully {len(self.swears)} swears and {len(self.punchlines)} puents.")

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"ERROR: Cannot load data for module swearer: {e}.")
    def _swear_up_text(self, text: str) -> str:
        # Private method to add swears and puent to text
        if not self.swears and not self.punchlines:
            return "Error: No data to edit, check file swear_data.json"
        
        words = text.split()
        num_words = len(words)

        if num_words == 0 :
            return ""
        # Swears logic
        max_curses = num_words // 2
        min_curses = max(0, num_words //5 - 1)
        num_curses = min(random.randint(min_curses, max_curses), len(self.swears)) # Checking if we are not exceeding limit of swears in file while randomizing

        if num_curses > 0:
            # Using self.swears from memory
            curses_to_insert = random.sample(self.swears, num_curses)
            for curse in curses_to_insert:
                insert_index = random.randint(0, len(words))
                words.insert(insert_index, curse)
            
        # Puents logic
        punchline = random.choice(self.punchlines) if self.punchlines else "" # Using punchlines from memory
        modified_text = " ".join(words) + " " + punchline

        return modified_text.strip()
    
    @app_commands.command(name="przeklinak", description="Dodaje przekleństwa i puenty do wiadomośći") #TODO language pack
    @app_commands.describe(text="Tekst do przerobienia(opcjonalnie, jeśli pusty - użyje ostatniej wiadomości)") #TODO language pack
    async def swear_command(self, interaction: discord.Interaction, text: Optional[str] = None):
        await interaction.response.defer(thinking=True)
        target_text = ""

        if text:
            target_text = text
        else:
            message_found = False
            # Searching for last message which is not command
            async for message in interaction.channel.history(limit=10):
                if (not message.author.bot or message.author.id == self.bot.user.id) and message.clean_content:
                    target_text = message.clean_content
                    message_found = True
                    break
            if not message_found:
                await interaction.followup.send("Nie udało mi się znaleźć ostatniej wiadomości do przerobienia", ephemeral=True)
                return
        edited_text = self._swear_up_text(target_text)
        if edited_text and edited_text.strip():
            await interaction.followup.send(edited_text)
        else:
            await interaction.followup.send("Nie udało się wygenerować odpowiedzi, spróbuj z innym tekstem.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Swearer(bot))