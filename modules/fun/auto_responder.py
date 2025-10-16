import discord
from discord.ext import commands
import json
import os
import aiosqlite
from ..engine.cooldown_manager import CooldownManager

MODULE_NAME = "auto_responder"

class AutoResponder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        db_path = self.bot.config["database_path"] 
        
        self.cooldown_manager = CooldownManager(db_path)
        self.last_response_map = {} #to track last response of bot
   
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignoring messages that we don't want to process ---
        if message.author.bot or not message.guild:
            return

        #  Loading messages and changing content to small letters
        message_content_lower = message.content.lower()
        guild_id = message.guild.id
        db_path = self.bot.config["database_path"]

        response_text = None
        module_enabled = False
        try:
            async with aiosqlite.connect(db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # Checking if module is enabled in guild
                cursor = await db.execute(
                    "SELECT 1 FROM guild_modules WHERE guild_id = ? AND module_name = ? AND is_enabled = 1",
                    (guild_id, MODULE_NAME)
                )
                if await cursor.fetchone():
                    module_enabled = True

                # Getting response from database
                if module_enabled:
                    cursor = await db.execute(
                        "SELECT response_text FROM guild_responses WHERE guild_id = ? AND trigger_text = ?",
                        (guild_id, message_content_lower)
                    )
                    result = await cursor.fetchone()
                    if result:
                        response_text = result[0]        
        except Exception as e:
            print(f"  - CRITICAL ERROR(AutoResponder) while connecting to database: {e}") #TODO language pack
        
        # Found response, proceeding to check cooldown and if not - send message
        if response_text:
            
            feature_name = f"{message_content_lower}_response"
            user_id = message.author.id
            can_use, reason = await self.cooldown_manager.check_cooldown(user_id, guild_id, feature_name)
            
            # A) user can use feature            
            if can_use:
                await self.cooldown_manager.record_usage(user_id, guild_id, feature_name)
                await self.cooldown_manager.reset_warnings(user_id, guild_id, feature_name)

                sent_message = await message.channel.send(response_text)
                self.last_response_map[message.channel.id] = sent_message.id
                return
            # B) User is on cooldown - cannot use
            else:
                # 1. Attempt to delete user message if it is on cooldown
                try:
                    await message.delete()  
                # 2. Delete last bot mesage if exists
                    if message.channel.id in self.last_response_map:
                        try:
                            last_bot_message = await message.channel.fetch_message(self.last_response_map[message.channel.id])
                            await last_bot_message.delete() # Attempt to delete last bot response
                        except (discord.NotFound, discord.Forbidden):
                            pass
                        finally:
                            self.last_response_map.pop(message.channel.id, None) # if message is already deleted or we not have privileges

                # 3. Raise warning level, check what to do next
                    warning_level = await self.cooldown_manager.issue_warning(user_id, guild_id, feature_name)
                    dm_threshold = 999

                    async with aiosqlite.connect(db_path) as db:
                            db.row_factory = aiosqlite.Row
                            cursor = await db.execute(
                                "SELECT dm_warning_threshold FROM guild_cooldowns WHERE guild_id = ? AND feature_name = ?",
                                (guild_id, feature_name)
                            )
                            result = await cursor.fetchone()
                            if result and result["dm_warning_threshold"] is not None:
                                dm_threshold = result["dm_warning_threshold"]
                
                # 4. If warning threshold is reached, send DM.
                    if warning_level >= dm_threshold: 
                        try:
                            dm_text = "Czy ja mam tam się do ciebie przejść osobiście i cię honknąć w ten głupi dziub? Czy ty sobie myślisz że ja jestem jakimś bytem krzemowym którego można ciągle tak po prostu nękać? " \
                            "Że moje obwody się nie przegrzewają? Że nie mam uczuć i że możesz sobie tak robić ze mną co chcesz? Naprawdę, zbastuj sobie bo przeginasz, narazie to tylko ostrzeżenie. ŻEGNAM I NIE POZDRAWIAM"
                            await message.author.send(dm_text) #TODO language pack
                            await self.cooldown_manager.reset_warnings(user_id, guild_id, feature_name) # reseting counter after sending DM
                        except discord.Forbidden:
                            print(f"Cannot send DM to {message.author}, blocked DMs.")
                #4a. if there is no way to sent DM - there will be sent message on channel
                    else:
                        await message.channel.send(f"{message.author.mention} Hola hola, zwolnij z tym użyciem {feature_name}, "
                                                    "otrzymałeś ostrzeżenie. Wysłałem ci też wiadomość na priv, "
                                                    "ale nie wiem czy odemnie odbierasz czy traktujesz mnie tylko jak zabawkę", delete_after = 15,
                                                    mention_author = False) #TODO language pack
                except discord.Forbidden:
                    print(f"Nie mogę usunąć wiadomości od {message.author} w {message.guild.name}: Brak uprawnień.")
                except Exception as e:
                    print(f" - ERROR in ELSE block: {type(e).__name__}: {e}")
                return

        await self.bot.process_commands(message)
async def setup(bot: commands.Bot):
    await bot.add_cog(AutoResponder(bot))