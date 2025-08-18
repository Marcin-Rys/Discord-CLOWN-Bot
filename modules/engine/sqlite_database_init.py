import aiosqlite 
import os

async def initialize_database(db_path: str):
    print(f"Initializing database in: {db_path}")

    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    try:
        async with aiosqlite.connect(db_path) as db:
            
            ## Table for role counters
            await db.execute("""
                CREATE TABLE IF NOT EXISTS role_counters (
                    guild_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    PRIMARY KEY (guild_id, role_id)
                )
            """)

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
            
            #table for cooldown warnings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cooldown_warnings (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    feature_name TEXT NOT NULL,
                    warning_level INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id, feature_name)
                )
            """)


            ## Table for guild settings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    notification_channel_id INTEGER
                )
            """)


            await db.commit()
            
        print("Database initialized succesfully")
    except Exception as e:
        print(f"Error during initialization of database: {e}")
        