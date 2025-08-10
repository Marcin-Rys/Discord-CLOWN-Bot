import asyncio
import json
import os


from typing import Optional, Dict
from dotenv import load_dotenv

import discord
from discord.ext import commands

from modules.engine.lang_utils import load_language_pack, get_translation
from modules.engine.sqlite_database_init import initialize_database

import logging 
handler = logging.StreamHandler()

# ==============================================================================
# HELPER FUNCTION SECTION 
# ==============================================================================
# Loading config
def load_config(filename: str = "config/config.json") -> Optional[Dict]: 
    """Loads the bot configuration from a JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}")
        return None
    
# Loading modules
def load_module_list(filename: str = "config/modules.json") -> list[str]:
    # Assigning modules(cogs) to be loaded from json file, returns only paths with "true"
    print("Loading module list to be loaded...") 
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            modules_to_load = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print (f"ERROR! Cannot load modules list ({filename}: {e})") 
        return [] #return blank list while error
    
    enabled_modules = []
    for folder,modules in modules_to_load.items(): #iterating through JSON file which has an {"folder":{"module": true/false}} structure
        for module_name, is_enabled in modules.items():
            if is_enabled:
                module_path = f"modules.{folder}.{module_name}" #creating full path in format "folder.module"
                enabled_modules.append(module_path)
    print(f"Found {len(enabled_modules)} modules to be loaded.") 
    return enabled_modules

# ==============================================================================
# BOT CLASS
# ==============================================================================
class DiscordBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = load_config()
        self.lang_pack = None # initializing with no language pack, we will load in main()

# ==============================================================================
# MAIN START FUNCTION
# ==============================================================================
async def main():
    """
    ## Logging for debugging purposes
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler() 
    ]
    )
    logging.getLogger("discord").setLevel(logging.DEBUG)
    """
    print("---MAIN BOT STARTUP INITIALIZED---")
    
    load_dotenv()
    
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("CRITICAL ERROR: No 'DISCORD_TOKEN' in .env file or enviromental variables.")
    
    # Intents initialization
    intents = discord.Intents.default() #setting up discord intents
    intents.message_content = True #need for modules reading messages
    intents.members = True #need for on_member_join
    
    bot = DiscordBot(command_prefix='!', intents=intents)

    if not bot.config: #load config if not close bot
        print("Cannot load config file. Closing bot.") 
        return

    # Loading language pack
    bot.lang_pack = load_language_pack(
        bot.config.get("language","en"), #for now loading en language
        bot.config["directories"]["lang_dir"]
    )

    if not bot.lang_pack:
        print("Error, cannot load language pack.") 
        return
    
    # Initialization of database
    data_dir = bot.config["directories"]["data_dir"]
    db_filename = bot.config["module_files"]["sqlite_database"]
    db_path = os.path.join(data_dir, db_filename)

    bot.config["database_path"] = db_path # Updating config with database path
    print(f"Initializing database at {db_path}...")
    await initialize_database(db_path)
    print(">>>Database initialized succesfully")

  
    ## Function to load modules from json file in config and create a list of selected with "True"
    modules_to_load = load_module_list()
    if not modules_to_load:
        print(f"WARNING: Not found any modules to be loaded. Bot will have no commands") 
    print("Loading modules(Cogs)...") 
    for module_path in modules_to_load:
        try:
            await bot.load_extension(module_path)
            print(f" - Loaded: {module_path}")
        except Exception as e: #we will send an more specific error 
            print(f" -- Loading error {module_path}:") 
            print(f"    {type(e).__name__}: {e}")
    print("\n--- STARTUP SEQUENCE DONE ---")
    print(">>> Trying to connect with Discord...")
   
    await bot.start(TOKEN) #token still in .env


# ==============================================================================
# SCRIPT ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    try: 
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot has been shutted down.") #TODO language pack