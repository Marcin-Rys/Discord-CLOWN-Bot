import aiosqlite
import json
from datetime import datetime, timedelta, timezone

class CooldownManager:
    def __init__(self, db_path: str, cooldown_configs: dict):
        self.db_path = db_path  # Assuming database path is set in config
        self.cooldown_configs = cooldown_configs

    async def check_cooldown(self, user_id: int, guild_id: int, feature_name: str) -> tuple[bool, str]:
        feature_config = self.cooldown_configs.get(feature_name) # downloads full configuration object
        if not feature_config:
            return True, ""
        
        rules = feature_config.get("limits")
        if not rules:
            return True, "" # no rules, no limit
        
        now = datetime.now(timezone.utc) 

        async with aiosqlite.connect(self.db_path) as db:
            for rule in rules:
                limit = rule['limit']
                period = timedelta(seconds=rule['period_seconds'])
                rule_name = rule.get('name', 'Unnamed Limit')

                start_time = now - period # time from which we are counting use of this rule

                cursor = await db.execute(
                    "SELECT COUNT(*) FROM command_usage WHERE user_id = ? AND guild_id = ? AND feature_name = ? AND timestamp >= ?",
                    (user_id, guild_id, feature_name, start_time.isoformat())
                )
                usage_count = (await cursor.fetchone())[0]

                if usage_count >= limit:
                    return False, f"(Przekroczono {rule_name.lower()})"
            return True, ""
    
    async def record_usage(self, user_id: int, guild_id: int, feature_name: str):
        ## Saves using function in database
        timestamp = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO command_usage (user_id, guild_id, feature_name, timestamp) VALUES (?, ?, ?, ?)",
                (user_id, guild_id, feature_name, timestamp)
            )
            await db.commit()

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