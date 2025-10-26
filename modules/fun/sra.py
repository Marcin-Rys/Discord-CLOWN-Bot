import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import Optional, Tuple
import json
from ..engine.cooldown_manager import CooldownManager

# --- HELPER FUNCTION ---
def process_sra_logic(text: str) -> tuple[Optional[str], Optional[str]]:
    """ 
    Modifying text by adding 'sra' prefix 
    returns(result_tekst, if_succeed)
    """
    if not text or not text.strip():
        return None, "sra:error_no_text_provided"

    words = text.split()
    #Step 1 - filtering candidates for words to be replaced
    potential_words = [word for word in words if 'a' in word.lower() and len(word) > 2 and not word.lower().endswith("sra")]

    if not potential_words:
        return None, "sra:error_no_words_found"
    
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
        return None, "sra:error_processing_text"

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
    return " ".join(words),None  # Joining the words back into a string

class Sra(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        db_path = self.bot.config["database_path"]  # Assuming database path is set in config
        self.cooldown_manager = CooldownManager(db_path)
        
    @app_commands.command(
            name= "shitify", 
            description=("Shits out an message by adding polish 'sra' prefix to a word.")
    )
    @app_commands.describe(
        text=("Add your own text to be shitted out!(optional)")
    )
    @app_commands.rename(text="text")

    async def sra(self, interaction: discord.Interaction, text: Optional[str] = None):
        translator = self.bot.tree.translator #using translator to get error messages

        if not interaction.guild:
            error_msg =  translator.get_translation("sra:error_notinguild", interaction.locale)
            await interaction.response.send_message(error_msg or "This command can only be used in a server", ephemeral=True)
            return
       
        await interaction.response.defer(thinking=True)  #Public defer as operation might take longer
        
        feature_name = "sra_command"
        can_use, reason = await self.cooldown_manager.check_cooldown(interaction.user.id, interaction.guild.id, feature_name)
        if not can_use:
            #await interaction.followup.send(contet=f"Hola hola, zwolnij! {reason}", ephemeral=True)
            error_msg = translator.get_translation("sra:error_cooldown", interaction.locale)
            await interaction.edit_original_response(content=(error_msg or "Slow down! {reason}"). format(reason=reason))
            await interaction.delete_original_response(delay=10)
            return

        target_text = text
        if not target_text:
            message_found = False
            async for message in interaction.channel.history(limit=10):
                if (not message.author.bot or message.author.id == self.bot.user.id) and message.clean_content:
                    target_text = message.clean_content
                    message_found = True
                    break
                    
            if not message_found:
                #deleting public thinking and then sending new ephemeric message
                error_msg = translator.get_translation("sra:error_nomsg", interaction.locale)
                await interaction.edit_original_response(content=error_msg or "I couldn't find any message to mess up.")
                await interaction.delete_original_response(delay=10)
                return

        result_text, error_key = process_sra_logic(target_text)

        if error_key :
            error_msg = translator.get_translation(error_key, interaction.locale)
            await interaction.delete_original_response()
            await interaction.followup.send(error_msg or "An error occured while processing the text.", ephemeral=True)
        else:
            await self.cooldown_manager.record_usage(interaction.user.id, interaction.guild.id, feature_name)
            await interaction.edit_original_response(content=result_text)

# --- STANDARD COG/MODULE SETUP ---
async def setup(bot: commands.Bot): # Standard setup function
    await bot.add_cog(Sra(bot))


