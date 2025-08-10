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
        ## Private method which search for letter "a/A" in word and it puts in random place "sra-"
        words = text.split()
        words_with_a = [word for word in words if 'a' in word.lower()] # Find an letters "a" or "A", ignore case

        if not words_with_a:
            return "W podanym tekście nie znaleziono słów z literą 'a'." #TODO language pack
        
        word_to_modify = random.choice(words_with_a)
        try:
            word_index = words.index(word_to_modify) # We remember word position
        except ValueError:
            return "Wystąpił błąd podczas modyfikacji tekstu."
        a_indices = [i for i, char in enumerate(word_to_modify) if char.lower() == 'a'] # We are finding all 'a' and 'A'

        if not a_indices: # If not found, return original
            return text
        
        chosen_a_index = random.choice(a_indices)

        ## New  modification, more funny!
        prefix = word_to_modify[:chosen_a_index]
        suffix = word_to_modify[chosen_a_index + 1:]
        modified_word = f"{prefix}sra{suffix}"

        words[word_index] = modified_word
        return " ".join(words)
    
    @app_commands.command(name="sra", description="W sposób bardzo inteligentny przerabia treść lub ostatnią wiadomość dodając prefix 'sra'.") #TODO language pack
    @app_commands.describe(text="Tekst do przerobienia(opcjonalnie, jeśli pusty - użyje ostatniej wiadomości)") #TODO language pack
    async def sra(self, interaction: discord.Interaction, text: Optional[str] = None):
        await interaction.response.defer(thinking=True) # Giving us time for background task
        
        feature_name = "sra_command"
        can_use, reason = await self.cooldown_manager.check_cooldown(interaction.user.id, interaction.guild.id, feature_name)
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


