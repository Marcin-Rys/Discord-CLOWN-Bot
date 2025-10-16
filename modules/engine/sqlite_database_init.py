import aiosqlite 
import os

async def initialize_database(db_path: str):
    print(f"Initializing database in: {db_path}")

    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    try:
        async with aiosqlite.connect(db_path) as db:
            
            # --- STATISTICS TABLES  ---
            ## Table for user stats
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_stats (
                        user_id INTEGER NOT NULL,
                        guild_id INTEGER NOT NULL,
                        message_count INTEGER DEFAULT 0,
                        PRIMARY KEY (user_id, guild_id)
                    )
            """)

            ## Table for commands usage stats
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS command_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        guild_id INTEGER NOT NULL,
                        feature_name TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                )
            """)

            # --- LANGUAGE SETTINGS ---
            # Table for language settings per guild
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS guild_language(
                        guild_id INTEGER PRIMARY KEY,
                        language_code TEXT NOT NULL DEFAULT 'en'         
                )
            """)

            # Table for language settings per user
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_language(
                        user_id INTEGER PRIMARY KEY,
                        language_code TEXT NOT NULL
                )
            """)

            # Table for custom server translations
            await db.execute("""
                CREATE TABLE IF NOT EXISTS custom_translations (
                    translation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    translation_key TEXT NOT NULL,
                    custom_text TEXT NOT NULL,
                    UNIQUE (guild_id, translation_key)
                )
            """)

            # --- COOLDOWNS/WARNIGNS ---
            # Table for cooldown warnings
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS cooldown_warnings (
                        user_id INTEGER NOT NULL,
                        guild_id INTEGER NOT NULL,
                        feature_name TEXT NOT NULL,
                        warning_level INTEGER DEFAULT 0,
                        PRIMARY KEY (user_id, guild_id, feature_name)
                )
            """)


            # --- GUILD SETTINGS ---
            # Table for enabling/disabling modules per server
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS guild_modules (
                        guild_id INTEGER NOT NULL,
                        module_name TEXT NOT NULL,
                        is_enabled BOOLEAN NOT NULL DEFAULT 1,
                        allow_in_dm BOOLEAN NOT NULL DEFAULT 1,
                        dm_warning_threshld INTEGER,
                        PRIMARY KEY (guild_id, module_name)
                )
            """)
            
            # Table for guild settings(notification channel for now)
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS guild_settings (
                        guild_id INTEGER PRIMARY KEY,
                        notification_channel_id INTEGER,
                        welcome_message TEXT
                )
            """)
    
            ## Table for role users counters
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS role_counters (
                        guild_id INTEGER NOT NULL,
                        role_id INTEGER NOT NULL,
                        channel_id INTEGER NOT NULL,
                        PRIMARY KEY (guild_id, role_id)
                    )
            """)
           
            # Table for bot responses(ex. Honk - bot will respond "HONK!" as message)
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS guild_responses (
                        response_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER NOT NULL,
                        trigger_text TEXT NOT NULL,
                        response_text TEXT NOT NULL,
                        UNIQUE (guild_id, trigger_text)
                )
            """)

            # Table for jokes
            await db.execute ("""
                    CREATE TABLE IF NOT EXISTS jokes (
                        joke_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER NOT NULL,
                        category TEXT NOT NULL,
                        text TEXT NOT NULL,
                        UNIQUE (guild_id, text)
                )
            """)

            # Table for cooldowns management
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS guild_cooldowns (
                        cooldown_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER NOT NULL,
                        feature_name TEXT NOT NULL,
                        limit_name TEXT,
                        limit_count INTEGER NOT NULL,
                        period_seconds INTEGER NOT NULL,
                        dm_warning_threshold INTEGER,
                        UNIQUE (guild_id, feature_name, period_seconds)    
                )
            """)

            # --- ROLE MANAGEMENT ---
            # Table which saves "role groups" to be choosen
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS role_groups (
                        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER NOT NULL,
                        group_name TEXT NOT NULL,
                        group_description TEXT,
                        UNIQUE (guild_id, group_name)
                )
            """)

            # Table for which roles can be chosen for each privileged group
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS selectable_roles (
                        selectable_role_id INTEGER PRIMARY KEY,
                        guild_id INTEGER NOT NULL,
                        group_id INTEGER NOT NULL,
                        role_id INTEGER NOT NULL,
                        role_description TEXT,
                        UNIQUE (group_id, role_id),
                        FOREIGN KEY (group_id) REFERENCES role_groups (group_id) ON DELETE CASCADE
                )
            """)
            
            # Table to change permissions for roles.
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS role_group_permissions (
                        permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER NOT NULL,
                        required_role_id INTEGER NOT NULL,
                        group_id INTEGER NOT NULL,
                        UNIQUE (guild_id, required_role_id, group_id)
                        FOREIGN KEY (group_id) REFERENCES role_groups (group_id) on DELETE CASCADE
                )         
            """)
            await db.commit()
            
        print("Database initialized succesfully")
    except Exception as e:
        print(f"Error during initialization of database: {e}")
        