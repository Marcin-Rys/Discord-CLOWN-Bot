import discord
from discord.ext import commands
from discord import app_commands
import random
import re
from typing import List

class DiceRoller(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dice_pattern = re.compile(r'(\d+)[dD](\d+)', re.IGNORECASE) # Pattern checker for "XdY" (ex. 1d6, 2d20), ignorecase makes that 'd' and 'D' is equal

    @app_commands.command(name="rzut", description="Rzuca kością w formacie 'XdY' (np. 2d6, 1d20).") #TODO language pack
    @app_commands.describe(dice="Wybierz standardowyrzut lub wpisz własny w formacie XdY.") #TODO language pack
    async def roll(self, interaction: discord.Interaction, dice: str):
        # 1. checking roll format with an regular expression
        match = self.dice_pattern.fullmatch(dice.strip()) 

        if not match:
            await interaction.response.send_message('Niepoprawny format. Użyj formatu "XdY" np. "2d6".', ephemeral=True) #TODO language pack
            return
        
        # 2. Downloading dice number and  dice walls
        rolls, limit = map(int, match.groups()) 

        # 3. Values validation 
        if rolls > 100 or limit > 1000:
          await interaction.response.send_message("Zbyt duże wartości, maksymalnie 100 kości i 1000 ścianek.", ephemeral=True) #TODO language pack
          return
        if rolls <= 0 or limit <= 0:
            await interaction.response.send_message("Liczba kości i ścianek musi być większa od zera.", ephemeral=True)
            return
        
        # 4. Rolling dices
        results = [random.randint(1,limit) for _ in range(rolls)]
        total_sum = sum(results)

        # 5. Creating and sending elegant message(Embed)
        embed = discord.Embed(
            title=f"🎲 Rzut kością: {rolls}d{limit}", #TODO language pack
            description=f"**Suma: {total_sum}**", #TODO language pack
            color=discord.Color.blue()
        )
        embed.set_author(name=f"Rzut wykonany przez: {interaction.user.display_name}", icon_url=interaction.user.avatar) #TODO language pack

        ## To avoid spam, show single rolls only for an decend amount of rolls
        if rolls <= 25:
            embed.add_field(name="Wyniki poszczególnych rzutów", value=", ".join(str(r) for r in results), inline=False) #TODO language pack
        else:
            embed.set_footer(text="Nie pokazano pojedyńczych rzutów z powodu ich liczby.") #TODO language pack

        await interaction.response.send_message(embed=embed)

    @roll.autocomplete('dice')
    async def roll_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        ## Prompting standard dice rolls
        standard_dice = [
                         "1d4","1d6", "1d8", "1d10", "1d12", "1d20", "1d100",
                         "2d4","2d6", "2d8", "2d10", "2d12", "2d20", "2d100",
                         "3d4","3d6", "3d8", "3d10", "3d12", "3d20", "3d100",
                         "4d4","4d6", "4d8", "4d10", "4d12", "4d20", "4d100",
                         "5d4","5d6", "5d8", "5d10", "5d12", "5d20", "5d100" 
                         ]
        # Return suggestions which are simillar to what user writed
        return [
            app_commands.Choice(name=dice, value=dice)
            for dice in standard_dice if current.lower() in dice.lower()
        ][:25] # Discord allows only 25 suggestions
    
async def setup(bot: commands.Bot): #standard setup function
    await bot.add_cog(DiceRoller(bot))