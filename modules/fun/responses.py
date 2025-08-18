import discord
from discord.ext import commands
import json
import os
from ..engine.cooldown_manager import CooldownManager

class MessageResponder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.responses = {} #initializing blank dictionary
        db_path = self.bot.config["database_path"] 
        cooldown_configs = {} 
       
        try:
            with open("config/cooldowns.json", 'r', encoding='utf-8') as f:
                cooldown_configs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"WARNING (MessageResponder Cog): cannot load cooldowns.json: {e}")
        
        self.cooldown_manager = CooldownManager(db_path, cooldown_configs)
      
        self._load_responses() #starting an method loading data only once, while Cog/module will initialize
        self.last_response_map = {} #to track last response of bot
    
    def _load_responses(self):
        config = self.bot.config
        filename = config["module_files"]["responses_file"]
        dir_path = config["directories"]["data_dir"]
        file_path = os.path.join(dir_path, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.responses = {key.lower(): value for key, value in json.load(file).items()} #loading responses and we will change keys for small letters.
            print(f"Loaded succesfully {len(self.responses)} responses.")
        except FileNotFoundError:
            print(f"Error! Not found file with responses: {file_path}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error! File with responses is damaged or has wrong format!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild: #1. Ignore messages from Bot itself(or other bots)
            return 
        
        message_content_lower = message.content.lower() #2. Load message and change it to small letters

        if message_content_lower in self.responses: #3. Check if message is in our dictionary loaded into memory
            feature_name = f"{message_content_lower}_response"
            user_id = message.author.id
            guild_id = message.guild.id

            can_use, reason = await self.cooldown_manager.check_cooldown(message.author.id, message.guild.id, feature_name)

            #A) - user can use feature 
            if can_use: #If user is not on cooldown, can use feature
                try:
                    await self.cooldown_manager.record_usage(user_id, guild_id, feature_name)
                    #Restarting warnings.
                    await self.cooldown_manager.reset_warnings(user_id, guild_id, feature_name)
                    
                    response_text = self.responses[message_content_lower]
                    sent_message = await message.channel.send(response_text) # Saving ID of bot response, to remove it later
                    self.last_response_map[message.channel.id] = sent_message.id
                    
                except Exception as e:
                    print(f" ERROR in block 'if can_use': {type(e).__name__}: {e}")
                return
            
            #B) user is on cooldown
            else:
                #1. Attempt to delete the user's message if on cooldown
                try:
                    await message.delete()  
                # 2. Delete last bot mesage if exists
                    if message.channel.id in self.last_response_map:
                        try:
                            last_bot_message = await message.channel.fetch_message(self.last_response_map[message.channel.id])
                            await last_bot_message.delete() # Attempt to delete last bot response
                            del self.last_response_map[message.channel.id] # remove also from map
                        except (discord.NotFound, discord.Forbidden):
                            pass
                        finally:
                            del self.last_response_map[message.channel.id] # if message is already deleted or we not have privileges

                    # 3. Raise warning level, check what to do next
                    warning_level = await self.cooldown_manager.issue_warning(user_id, guild_id, feature_name)
                    dm_threshold = self.cooldown_manager.cooldown_configs.get(feature_name, {}).get("dm_warning_threshold", 999) #Download threshold from config

                    # 4. If warning threshold is reached, send DM.
                    if warning_level >= dm_threshold: 
                        try:
                            await message.author.send("Czy ja mam tam się do ciebie przejść osobiście i cię honknąć w ten głupi dziub? Czy ty sobie myślisz że ja jestem jakimś bytem krzemowym którego można ciągle tak po prostu nękać?"
                                                    "Że moje obwody się nie przegrzewają? Że nie mam uczuć i że możesz sobie tak robić ze mną co chcesz?"
                                                    "Naprawdę, zbastuj sobie bo przeginasz, narazie to tylko ostrzeżenie. ŻEGNAM I NIE POZDRAWIAM") #TODO language pack
                            await self.cooldown_manager.reset_warnings(user_id, guild_id, feature_name) # reseting counter after sending DM
                        except discord.Forbidden:
                            print(f"Cannot send DM to {message.author}, blocked DMs.")
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
    await bot.add_cog(MessageResponder(bot))
