import discord
from discord import app_commands
import json
import os
# import aiosqlite - for now not using it
from typing import Optional

class BotTranslator(app_commands.Translator):
    def __init__(self, lang_dir: str):
        self.lang_dir = lang_dir
        self.translations = {}
        self._load_all_languages()

    # Loads all language packs in bot startup
    def _load_all_languages(self): 
        print(f"Loading languages from folder: {self.lang_dir}")
        if not os.path.isdir(self.lang_dir):
            print(f"Language directory {self.lang_dir} does not exist. Translations will not work")
            return

        for lang_code in os.listdir(self.lang_dir):
            lang_path = os.path.join(self.lang_dir, lang_code)
            if os.path.isdir(lang_path):
                self.translations[lang_code] = {}
                for filename in os.listdir(lang_path):
                    if filename.endswith(".json"):
                        module_name= filename[:-5].lower()
                        file_path = os.path.join(lang_path, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if content:
                                    self.translations[lang_code][module_name] = json.loads(content)
                                else:
                                    print(f"WARNING! Translation file is empty: {file_path}")
                        except json.JSONDecodeError as e:
                                print(f" ERROR: Translation file is damaged(not valid JSON format): {file_path}. Error:{e}")
        print(f"Loaded languages: {list(self.translations.keys())}")

    def get_translation(self, key: str, locale: discord.Locale, fallback: str="Translation error") -> str:
        lang_code = str(locale).split('-')[0] #Simplyfying locale to be just "pl" or "en"
        
        try: 
            module_name, string_key = key.split(":",1)
            module_name = module_name.lower()
        except ValueError:
            return fallback
        

        #Trying to find translation from user language.
        translation = self.translations.get(lang_code, {}).get(module_name, {}).get(string_key)
        if translation is not None:
            return translation
        
        fallback_translation = self.translations.get("en",{}).get(module_name,{}).get(string_key) #Fallback to english if user language not found
        if fallback_translation is None:
            return fallback_translation
        
        return fallback
    
    async def translate(self, string: app_commands.locale_str, locale: discord.Locale, context: app_commands.TranslationContext) -> Optional[str]:
        #function only used by discord.py internally to getranslation for app_commands.locale_str - app comands
        key = string.message

        return self.get_translation(key, locale, fallback=None) # if no translation found return None to use an command default string
    
''' - FOR FUTURE USE WITH AIOSQLITE AND CUSTOM TRANSLATIONS
    async def get_translation(self, key: str, interaction: discord.Interaction, fallback: str = None) -> str:
        module, string_key = key.split(":", 1)
        guild_id = interaction.guild.id if interaction.guild else None
        
        # 1. Checking non-standard guild translations
        if guild_id:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT custom_text FROM custom_translations WHERE guild_id = ? AND translation_key = ?",
                    (guild_id, key)
                )
                custom = await cursor.fetchone()
                if custom:
                    return custom[0]

        # 2. Checking user preferences
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT language_code FROM user_language WHERE user_id = ?", (interaction.user.id,))
            user_lang_row = await cursor.fetchone()
            if user_lang_row:
                user_lang = user_lang_row[0]
                translation = self.translations.get(user_lang, {}).get(module, {}).get(string_key)
                if translation:
                    return translation            
        # 3. Checking server preferences
        if guild_id:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT language_code FROM guild_language WHERE guild_id = ?", (guild_id,))
                guild_lang_row = await cursor.fetchone()
                if guild_lang_row:
                    guild_lang = guild_lang_row[0]
                    translation = self.translations.get(guild_lang, {}).get(module, {}).get(string_key)
                    if translation:
                        return translation
                
        #4. Return to default language
        default_lang = self.config.get("default_language, en")       
        return default_lang or fallback or key
'''