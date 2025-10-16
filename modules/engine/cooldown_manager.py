import aiosqlite
from datetime import datetime, timedelta, timezone

class CooldownManager:
    def __init__(self, db_path: str):
        self.db_path = db_path  # Assuming database path is set in config
        print("---DEBUG(CooldownManager): CooldownManager (Database-drive) succesfully initialized ---")
    async def check_cooldown(self, user_id: int, guild_id: int, feature_name: str) -> tuple[bool,str]:
        #Check if user is on cooldown by downloading rules from database, returns (can_use, reason)

        rules = []
        #1. Download all cooldown rules for this function on guild
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row #allows access to colums per name
                cursor = await db.execute(
                    "SELECT limit_name, limit_count, period_seconds FROM guild_cooldowns WHERE guild_id = ? AND feature_name = ?",
                    (guild_id, feature_name)
                )
                rules = await cursor.fetchall()
        except Exception as e:
            print(f"CRITICAL ERROR(CooldownManager): Cannot download rules for cooldown from database {e}")
            return True, "" #In case of database error allow usage
        
        if not rules:
            return True, "" #No rules in database = no limit
        
        now = datetime.now(timezone.utc)

        #2. Check all rules
        async with aiosqlite.connect(self.db_path) as db:
            for rule in rules:
                limit = rule['limit_count']
                period = timedelta(seconds=rule['period_seconds'])
                rule_name = rule['limit_name'] or "Unnamed limit"

                start_time = now - period
                
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM command_usage WHERE user_id = ? AND guild_id = ? AND feature_name = ? AND timestamp >= ?",
                    (user_id, guild_id, feature_name, start_time.isoformat())
                )
                usage_count = (await cursor.fetchone())[0]

                if usage_count >= limit:
                    reason = f"Limit exceeded {rule_name.lower()}"
                    return False, reason
                
        return True, ""
    
    async def record_usage(self, user_id: int, guild_id: int, feature_name: str):
        ## Saves using function in database
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO command_usage (user_id, guild_id, feature_name, timestamp) VALUES (?, ?, ?, ?)",
                    (user_id, guild_id, feature_name, timestamp)
                )
                await db.commit()
        except Exception as e:
            print(f"CRITICAL ERROR(CooldownManager): Cannot save usage of command to database: {e}")

    async def issue_warning(self, user_id: int, guild_id: int, feature_name: str) -> int:
        """
        Raises an warning for the user and returns new level of warning.
        Resets warnings after 24hours after last try(optional)
        """

        async with aiosqlite.connect(self.db_path) as db:
           # we are using INSER... ON CONFLICT... UPDATE, to update counter
            await db.execute("""
                INSERT INTO cooldown_warnings (user_id, guild_id, feature_name, warning_level)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id, guild_id, feature_name)
                DO UPDATE SET warning_level = warning_level +1
                """,
                (user_id, guild_id, feature_name)
            )

            #download updated warning level
            cursor = await db.execute(
                "SELECT warning_level FROM cooldown_warnings WHERE user_id = ? AND guild_id = ? AND feature_name = ?",
                (user_id, guild_id, feature_name)
            )
            result = await cursor.fetchone()
            await db.commit()

            return result[0] if result else 0
        
    async def reset_warnings(self, user_id: int, guild_id: int, feature_name: str):
        # Resets warning for user for such function"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM cooldown_warnings WHERE user_id = ? AND guild_id = ? AND feature_name = ?",
                (user_id, guild_id, feature_name)
            )
            await db.commit()