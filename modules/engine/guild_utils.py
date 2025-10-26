import discord
import aiosqlite


# Function that gets list of servers where user and bots are together and on which module is enabled and allowed to respond in DMs
async def get_accessible_guilds_for_feature(bot, user: discord.User, module_name: str) -> list[discord.Guild]:
    
    accessible_guilds = []
    db_path = bot.config["database_path"]


    for guild in bot.guilds:
        if guild.get_member(user.id) is not None:
            try:
                async with aiosqlite.connect(db_path) as db:
                    db.row_factory = aiosqlite.Row
                    cursor = await db.execute(
                        "SELECT 1 FROM guild_modules WHERE guild_id = ? AND module_name = ? AND is_enabled = 1 AND allow_in_dm = 1",
                        (guild.id, module_name)
                    )
                    if await cursor.fetchone():
                        accessible_guilds.append(guild)
            except Exception as e:
                print(f"#guild_utils.py | ERROR! | Error while checking availability of module '{module_name} for server {guild.id}: {e}")
    return accessible_guilds
