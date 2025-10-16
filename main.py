import asyncio
import json
import os

from typing import Optional, Dict
from dotenv import load_dotenv

import discord
from discord.ext import commands

from modules.engine.translator import BotTranslator
from modules.engine.sqlite_database_init import initialize_database

import logging 

# ==============================================================================
# LOADING ENVIROMENTAL VARIABLES
# ==============================================================================
load_dotenv()
DB_PATH = os.getenv('DB_PATH')
MODULES_CONFIG_PATH = os.getenv('MODULES_CONFIG_PATH')
CONFIG_PATH = os.getenv('CONFIG_PATH')
LANG_DIR = os.getenv('LANG_DIR', 'lang')
DATA_DIR = os.getenv("DATA_DIR", 'data')
DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE')


# ==============================================================================
# HELPER FUNCTION SECTION 
# ==============================================================================

# Loadings module/cogs list to be loaded to bot, from JSON
def load_module_list() -> list[str]:
    filename = os.getenv('MODULES_CONFIG_PATH')
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            modules_to_load = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print (f"CRITICAL ERROR: Couldn't find database with module list ({filename}: {e})")
        return []
    
    enabled_modules =[]
    for folder, modules in modules_to_load.items():
        for module_name, is_enabled in modules.items():
            if is_enabled:
                module_path = f"modules.{folder}.{module_name}"
                enabled_modules.append(module_path)
    print(f"Found {len(enabled_modules)} modules to be loaded.")
    return enabled_modules

# ==============================================================================
# BOT CLASS
# ==============================================================================
class DiscordBot(commands.Bot):
    def __init__(self, config: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.lang_pack = None # initializing with no language pack, we will load in main()

# ==============================================================================
# MAIN START FUNCTION
# ==============================================================================
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    #logging.getLogger("discord").setLevel(logging.DEBUG)
    print("---MAIN BOT STARTUP INITIALIZED---")
    
    # Checking if token is setted up.
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("CRITICAL ERROR: No 'DISCORD_TOKEN' in .env file or enviromental variables.")
        return
    
    if not all([TOKEN, DB_PATH, MODULES_CONFIG_PATH, CONFIG_PATH, LANG_DIR, DATA_DIR, DEFAULT_LANGUAGE]):
            print("CRITICAL ERROR: Missing one or more crucial enviromental variables in .env")
            print("Check if there is defined: DISCORD_TOKEN, DB_PATH, MODULES_CONFIG_PATH, LANG_DIR, DEFAULT_LANGUAGE")
            print("\n--- DEBUG: Sprawdzanie wczytanych zmiennych środowiskowych ---")
            print(f"TOKEN: {TOKEN}")
            print(f"DB_PATH: {DB_PATH}")
            print(f"MODULES_CONFIG_PATH: {MODULES_CONFIG_PATH}")
            print(f"CONFIG_PATH: {CONFIG_PATH}")
            print(f"LANG_DIR: {LANG_DIR}")
            print(f"DEFAULT_LANGUAGE: {DEFAULT_LANGUAGE}")
            print("----------------------------------------------------------\n")

            return
    
    config = {}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"CRITICAL ERROR: Cannot find configuration file in: ({CONFIG_PATH}): {e}")
        return
    
    #inputting crucial paths and settings from .env to "config" dictionary
    config["database_path"] = DB_PATH
    config["lang_dir"] = LANG_DIR
    config["default_language"] = DEFAULT_LANGUAGE 
    config["data_dir"] = DATA_DIR

    # Intents initialization
    intents = discord.Intents.default() #setting up discord intents
    intents.message_content = True #need for modules reading messages
    intents.members = True #need for on_member_join
    bot = DiscordBot(config=config, command_prefix='!', intents=intents)

    # Database initialization
    print(f"Initializing database in: {DB_PATH}...")
    await initialize_database(DB_PATH)
    print(">>>Database initialized succesfully.")

    # Language translator initialization\
    print(f"Initializing translations from folder: {LANG_DIR}...")
    translator = BotTranslator(lang_dir=LANG_DIR)
    await bot.tree.set_translator(translator)
    print(">>> Translations initialized succesfully.")
  
    # Loading Cogs/Modules
    modules_to_load = load_module_list()
    print("\nLoaduin modules(Cogs)...")
    for module_path in modules_to_load:
        try:
            await bot.load_extension(module_path)
            print(f" - Loaded: {module_path}")
        except Exception as e:
            print(f" -- Error while loading {module_path}:")
            print(f"    {type(e).__name__}: {e}")
    print("\n--- STARTUP SEQUENCE DONE ---")
    print(">>> Trying to connect with Discord...")

    await bot.start(TOKEN)


# ==============================================================================
# SCRIPT ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    try: 
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot has been shutted down.") #TODO language pack