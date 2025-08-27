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


            # --- GUILD CHANNELS SETTINGS ---
            ## Table for guild settings(notification channel for now)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    notification_channel_id INTEGER
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

            # --- ROLE MANAGEMENT ---
            # Table which saves "role groups" to be choosen
            await db.execute("""
                CREATE TABLE IF NOT EXISTS role_groups (
                             group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             guild_id INTEGER NOT NULL,
                             group_name TEXT NOT NULL UNIQUE,
                             group_description TEXT
                             )
                        """)

            # Table for which roles can be chosen for each privileged group
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS selectable_roles (
                             selectable_role_id INTEGER PRIMARY KEY,
                             group_id INTEGER NOT NULL,
                             role_id INTEGER NOT NULL,
                             role_description TEXT,
                             FOREIGN KEY (group_id) REFERENCES role_groups (group_id) ON DELETE CASCADE
                             )
                             """)
            
            await db.execute("""
                    CREATE TABLE IF NOT EXISTS role_group_permissions (
                        permission_id INTEGER PRIMARY KEY,
                             required_role_id INTEGER NOT NULL,
                             group_id INTEGER NOT NULL,
                             guild_id INTEGER NOT NULL,
                             FOREIGN KEY (group_id) REFERENCES role_groups (group_id) on DELETE CASCADE
                        )         
                    """)
            await db.commit()
            
        print("Database initialized succesfully")
    except Exception as e:
        print(f"Error during initialization of database: {e}")
        