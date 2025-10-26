import discord
from discord.ext import commands
import aiosqlite


class RoleCounter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = self.bot.config["database_path"]  # Assuming database path is set in config

    async def update_counter(self, guild_id: int, role_id: int):
        guild = self.bot.get_guild(guild_id)
        role = guild.get_role(role_id)
        if not guild or not role:
            #deleting from database server/role that has been already deleted
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM role_counters WHERE guild_id = ? and role_id = ?",(guild_id, role_id))
                await db.commit()
            return
    
        async with aiosqlite.connect(self.db_path) as db: 
          async with db.execute("SELECT channel_id FROM role_counters WHERE guild_id = ? AND role_id = ?",(guild_id, role_id)) as cursor:
            result = await cursor.fetchone()
            if not result:
                return
            channel_id = result[0]

        channel = guild.get_channel(channel_id)
        if not channel:
            #deleting from database channel that has been already deleted
            async with aiosqlite.connect(self.db_path) as db:
               await db.execute("DELETE FROM role_counters WHERE role_id = ?", (role_id,))
               await db.commit()
            return
        
        count = len(role.members)
        new_name = f"{role.name}: {count}"

        try:
            if channel.name != new_name:
                await channel.edit(name=new_name, reason="Automatic update of role counter")
        except discord.errors.Forbidden:
            print(f"#role_counter.py | Error! | No privileges to edit channel {channel.name} on server {guild.name}")
        except Exception as e:
            print(f"Unexpected error during refreshing channel: {e}")


    @commands.Cog.listener()
    async def on_ready(self):
        print("#role_counter.py | Ready, starting update of role counters in background...")
        self.bot.loop.create_task(self.update_all_counters(), name="UpdateAllRoleCounters")
    
    async def update_all_counters(self):
    ###updating counters after bot startup###
        await self.bot.wait_until_ready()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT guild_id, role_id FROM role_counters") as cursor:
                    all_counters = await cursor.fetchall()

                    if not all_counters:
                        print("#role_counter.py | WARNING | No role counters found in the database to update")
                        return
                    print(f"#role_counter.py | Found {len(all_counters)} role counters to update")
                    
                    for guild_id, role_id in all_counters:
                        await self.update_counter(guild_id,role_id)

            print("#role_counter.py | Task 'UpdateAllRoleCounters' finished succesfully.")
        except Exception as e:
            print(f"#role_counter.py | WARNING! |An error occured in the 'UpdateAllCounters' task: {e}")
   
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        ###check outs role change for user
        if before.roles == after.roles:
            return

        changed_roles = set(before.roles) ^ set(after.roles)
        guild_id = after.guild.id

        for role in changed_roles:
            await self.update_counter(guild_id, role.id)
   
   
async def setup(bot: commands.Bot):
    await bot.add_cog(RoleCounter(bot))

        

        