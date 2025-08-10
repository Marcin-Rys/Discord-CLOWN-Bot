import json
import os
from typing import Dict, Any, Optional


def load_language_pack(lang_code: str, lang_dir: str) -> Dict:
    """Loads a language pack from a JSON file."""
    lang_file = os.path.join(lang_dir, f"{lang_code}.json")
    try:
        with open(lang_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Language file not found: {lang_file}") #critical error prompt
        return {}  
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in language file: {lang_file}") #critical error prompt
        return {}

def get_translation(key: str, language_pack: Dict, module: Optional[str] = None, submodule: Optional[str] = None, **kwargs: Any) -> str:
    """
    Retrieves a translation from the loaded language pack.
    Handles missing translations and formatting.

    Args:
        key: The translation key.
        language_pack: The loaded language pack.
        module: The primary module (e.g., 'fun', 'administrative').
        submodule: The submodule within the module (e.g., 'swearer', 'jokes').
        **kwargs:  Arguments for string formatting.

    Returns:
        The translated string, or the key itself if no translation is found.
    """

    if not language_pack:
        print("Warning: Language pack not loaded.  Using default (English) keys.")
        return key

    translation = None

    # 1. try specific module and submodule
    if module and submodule:
        try:
            translation = language_pack["modules"][module][submodule][key]
        except (KeyError, TypeError):
            pass #Ignore and try other locations
    # 2. Try module without submodule
    if translation is None and module:
        try: translation = language_pack["modules"][module][key]
        except (KeyError, TypeError):
            pass
    # 3. Try engine.general
    if translation is None:
        try:
            translation = language_pack["modules"]["engine"]["general"][key]
        except(KeyError, TypeError):
            pass
    #4. Try general_errors(top level)
    if translation is None:
        try:
            translation = language_pack["general_errors"][key]
        except(KeyError, TypeError):
            pass
    #5. If still not found, return the key
    if translation is None:
        print(f"Warning: Translation not found for key: '{key}'")
        return key.format(**kwargs) if kwargs else key
    
    return translation.format(**kwargs) if kwargs else key