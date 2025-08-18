import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import Optional
import json
from ..engine.cooldown_manager import CooldownManager

class Sra(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        db_path = self.bot.config["database_path"]  # Assuming database path is set in config
        cooldown_configs = {}
        try:
            with open("config/cooldowns.json", 'r', encoding='utf-8') as f:
                cooldown_configs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Cannot (Sra module): cannot load cooldowns file: {e}")
        self.cooldown_manager = CooldownManager(db_path, cooldown_configs)
    def _sra_text(self, text: str) -> str:
        """ Private method to modify text by adding 'sra' prefix """
        
        words = text.split()
        #Step 1 - filtering candidates for words to be replaced
        potential_words = [word for word in words if 'a' in word.lower() and len(word) > 2 and not word.lower(endswith("sra"))]

        if not potential_words:
            return "W podanym tekście nie znalazłem żadnych słów do przerobienia."  #TODO language pack
        
        #Step 2 - Prioritizing words by points 
        best_word = None
        highest_score = -1

        for word in potential_words:
            score = 0
            if len(word) > 4:
                score += 2 # Longer words get more points

            score += 3 * word.lower().count('a')  # Each 'a' in word gives 3 points

            if word.lower().count('a') == 1 and word.lower().endswith('a'):
                score -= 4 # If word ends with 'a' and has only one 'a', it gets -4 points
            
            #checking if this is the best word so far
            if score > highest_score:
                highest_score = score
                best_word = word 

        if best_word is None:
            best_word = random.choice(potential_words)  # Fallback to random word if no best found


        #Step 3 - Replacing the best word with 'sra' version
        try:
            word_index = words.index(best_word)
        except ValueError:
            return "Wystąpił błąd podczas modyfikacji textu."  #TODO language pack

        a_indices = [i for i, char in enumerate(best_word) if char.lower() == 'a'] #checking all 'a' in word.

        #Giving more chance to select 'a' closer to the beginning of word. We are waged list where first 'a' has more chance to be selected.
        weights = [len(a_indices) - i for i in range(len(a_indices))]
        chosen_a_index = random.choices(a_indices, weights=weights, k=1)[0]

        # saving the suffix of 'a' word
        suffix = best_word[chosen_a_index:]

        if best_word[0].isupper():
            modified_word = "Sra" + suffix
        else:
            modified_word = "sra" + suffix

        #Step 4 - returning an edited text
        words[word_index] = modified_word  # Replacing the word in the list
        return " ".join(words)  # Joining the words back into a string


    
    @app_commands.command(name="sra", description="W sposób bardzo inteligentny przerabia treść lub ostatnią wiadomość dodając prefix 'sra'.") #TODO language pack
    @app_commands.describe(text="Tekst do przerobienia(opcjonalnie, jeśli pusty - użyje ostatniej wiadomości)") #TODO language pack
    async def sra(self, interaction: discord.Interaction, text: Optional[str] = None):
        await interaction.response.defer(thinking=True, ephemeral=True) # Giving us time for background task

        feature_name = "sra_command"
        can_use, reason = await self.cooldown_manager.check_cooldown(interaction.user.id, interaction.guild.id, feature_name)
        feature_name = "sra_command"
        can_use, reason = await self.cooldown_manager.check_cooldown(interaction.user.id, interaction.guild.id, feature_name)
            await interaction.followup.send_message(f"Hola hola, zwolnij z użyciem!, {reason}", ephemeral=True)
        if not can_use:
            await interaction.response.send_message(f"Hola hola, zwolnij z użyciem!, {reason}", ephemeral=True)
            return
        
        target_text = ""
        if text:
            target_text = text # If user specified text
        else:
            message_found= False
            async for message in interaction.channel.history(limit=10): # Searching for message which is not command
                if (not message.author.bot or message.author.id == self.bot.user.id) and message.clean_content:
                    target_text = message.clean_content
                    message_found = True
                    break
            if not message_found:
                await interaction.followup.send("Nie znalazłem żadnej wiadomości do przerobienia.", ephemeral=True) #TODO language pack
                return
        
        await self.cooldown_manager.record_usage(interaction.user.id, interaction.guild.id, feature_name) # Recording usage of command
       
        edited_text = self._sra_text(target_text) # Modifying text
        if edited_text and edited_text.strip():
            await interaction.followup.send(edited_text)
        else:
            await interaction.followup.send("Nie udało się wygenerować odpowiedzi, spróbuj z innym tekstem.", ephemeral=True) #TODO language pack

async def setup(bot: commands.Bot): # Standard setup function
    await bot.add_cog(Sra(bot))


