import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import Optional
import json
from ..engine.cooldown_manager import CooldownManager

# --- HELPER FUNCTION ---
def process_sra_logic(self, text: str) -> tuple[str, bool]:
    """ 
    Modifying text by adding 'sra' prefix 
    returns(result_tekst, if_succeed)
    """
    
    words = text.split()
    #Step 1 - filtering candidates for words to be replaced
    potential_words = [word for word in words if 'a' in word.lower() and len(word) > 2 and not word.lower().endswith("sra")]

    if not potential_words:
        return "W podanym tekście nie znalazłem żadnych słów do przerobienia.", False  #TODO language pack
    
    #Step 2 - Prioritizing words by points 
    best_word = None
    highest_score = -1
    for word in potential_words:
        score = 0
        
        if len(word) > 4: # Longer words get more points
            score += 2 
        
        score += 3 * word.lower().count('a')  # Each 'a' in word gives 3 points

        if word.lower().count('a') == 1 and word.lower().endswith('a'): # If word ends with 'a' and has only one 'a', it gets -4 points
            score -= 4 
        
        if score > highest_score: #checking if this is the best word so far
            highest_score = score
            best_word = word 

    if best_word is None: best_word = random.choice(potential_words)  # Fallback to random word if no best found


    #Step 3 - Replacing the best word with 'sra' version
    try:
        word_index = words.index(best_word)
    except ValueError:
        return "Wystąpił błąd podczas modyfikacji textu.", False  #TODO language pack

    a_indices = [i for i, char in enumerate(best_word) if char.lower() == 'a'] #checking all 'a' in word.

    #Giving more chance to select 'a' closer to the beginning of word. We are waged list where first 'a' has more chance to be selected.
    weights = [len(a_indices) - i for i in range(len(a_indices))]
    chosen_a_index = random.choices(a_indices, weights=weights, k=1)[0]

    # saving the suffix of 'a' word
    suffix = best_word[chosen_a_index + 1:]

    if best_word[0].isupper():
        modified_word = "Sra" + suffix
    else:
        modified_word = "sra" + suffix

    #Step 4 - returning an edited text
    words[word_index] = modified_word  # Replacing the word in the list
    return " ".join(words),True  # Joining the words back into a string

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
        
    @app_commands.command(name="sra", description="W sposób bardzo inteligentny przerabia treść lub ostatnią wiadomość dodając prefix 'sra'.") #TODO language pack
    @app_commands.describe(text="Tekst do przerobienia(opcjonalnie, jeśli pusty - użyje ostatniej wiadomości)") #TODO language pack
    async def sra(self, interaction: discord.Interaction, text: Optional[str] = None):

        #--- Step 1: Validation if user can use command and not exceed limit ---
        feature_name = "sra_command"
        can_use, reason = await self.cooldown_manager.check_cooldown(interaction.user.id, interaction.guild.id, feature_name)
        if not can_use:
            await interaction.response.send_message(f"Hola hola, zwolnij z użyciem!, {reason}", ephemeral=True)
            return

        #--- Step 2: Downloading data ---
        target_text = ""
        responder = interaction.response

        if text:
            target_text = text
        else:
            await interaction.response.defer(thinking=True) #Searching history is slow, we need to use defer, we are using public one as we are reaching for success...
            responder = interaction.followup

            message_found = False
            async for message in interaction.channel.history(limit=10): #Logic for searching in history
                if (not message.author.bot or message.author.id == self.bot.user.id) and message.clean_content:
                    target_text = message.clean_content
                    message_found = True
                    break
            if not message_found:
                await responder.send("Nie znalazłem żadnej wiadomości do przerobienia", ephemeral=True) #Error is always ephemeral, we are using 'responder' which is now followup
                return
            
        # -- Step 3: Editing and reply ---
        # Querying helper function which will return up an result and success flag
        result_text, was_succesful = process_sra_logic(target_text)

        if was_succesful:
            await self.cooldown_manager.record_usage(interaction.user.id, interaction.guild.id, feature_name)
            await responder.send(result_text)
        else:
            await responder.send(result_text, ephemeral=True)

# --- STANDARD COG/MODULE SETUP ---
async def setup(bot: commands.Bot): # Standard setup function
    await bot.add_cog(Sra(bot))


