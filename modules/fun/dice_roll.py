import discord
from discord.ext import commands
from discord import app_commands
import random
import re
from typing import List

_ = app_commands.locale_str

class DiceRoller(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dice_pattern = re.compile(r'(\d+)[dD](\d+)', re.IGNORECASE) # Pattern checker for "XdY" (ex. 1d6, 2d20), ignorecase makes that 'd' and 'D' is equal

    @app_commands.command(
        name=_("roll", key="dice_roll:command_name"), 
        description=_("Rolls a dice, use format 'XdY' (ex. 2d6, 1d20)", key="dice_roll:command_description")
    )
    @app_commands.describe(
        dice=_("Choose standard role or input your own in format XdY(ex. 2d6; 3d20).", key="dice_roll:option_dice_description")
    ) 
    async def roll(self, interaction: discord.Interaction, dice: str):
        # 1. checking roll format with an regular expression
        match = self.dice_pattern.fullmatch(dice.strip()) 

        #initializing translator
        translator = self.bot.translator

        if not match:
            error_msg = translator.get_translation("dice_roll:error_incorrect_format", interaction.locale)
            await interaction.response.send_message(error_msg, ephemeral=True)
            return
        
        # 2. Downloading dice number and  dice walls
        rolls, limit = map(int, match.groups()) 

        # 3. Values validation 
        if rolls > 100 or limit > 1000:
            error_msg = translator.get_translation("dice_roll:error_values_toomuch", interaction.locale)
            await interaction.response.send_message(error_msg , ephemeral=True) 
            return
        if rolls <= 0 or limit <= 0:
            error_msg = translator.get_translation("dice_roll:error_values_toosmall", interaction.locale)
            await interaction.response.send_message("", ephemeral=True)
            return
        
        # 4. Rolling dices
        results = [random.randint(1,limit) for _ in range(rolls)]
        total_sum = sum(results)

        #translations for embed
            
        embed_title = translator.get_translation(
            "dice_roll:embed_title",
            interaction.locale,
            rolls=rolls,
            limit=limit
        )
        embed_description = translator.get_translation(
            "dice_roll:embed_description",
            interaction.locale,
            total_sum=total_sum
        )

        embed_author = translator.get_translation(
            "dice_roll:embed_author",
            interaction.locale,
            user_name=interaction.user.display_name
        )
        # 5. Creating and sending elegant message(Embed)
        embed = discord.Embed(
            title=embed_title,
            description=embed_description,
            color=discord.Color.blue()
        )
        embed.set_author(name=embed_author, icon_url=interaction.user.avatar)

        ## To avoid spam, show single rolls only for an decend amount of rolls
        if rolls <= 25:
            field_name = translator.get_translation("dice_roller:embed_field_name", interaction.locale)
            embed.add_field(name=field_name, value=", ".join(str(r) for r in results), inline=False)
        else:
            footer_text = translator.get_translation("dice_roll:embed_footer_toomany", interaction.locale)
            embed.set_footer(text=footer_text)

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