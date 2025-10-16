import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View
import aiosqlite

# --- UI components ---

class RoleSelectMenu(Select):
    def __init__(self, bot, user_roles, selectable_roles_data):
        self.bot = bot
        options = []
        for role_id, role_description in selectable_roles_data:
            role = bot.get_guild(user_roles[0].guild.id).get_role(role_id)
            if role:
                #Checking if user already has a role
                is_selected = role in user_roles
                options.append(discord.SelectOption(
                    label=role.name,
                    value=str(role.id),
                    description=role_description,
                    default=is_selected
                ))
        super().__init__(
            placeholder="Check roles which you want to have...",
            min_values=0,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        selected_role_ids = {int(value) for value in self.values}

        all_selectable_roles_in_menu = {int(opt.value) for opt in self.options}

        roles_to_add = {role_id for role_id in selected_role_ids if member.get_role(role_id) is None}
        roles_to_remove = {role_id for role_id in all_selectable_roles_in_menu if role_id not in selected_role_ids and member.get_role(role_id) is not None}

        guild = member.guild
        final_add = [guild.get_role(role_id) for role_id in roles_to_add]
        final_remove = [guild.get_role(role_id) for role_id in roles_to_remove]

        try:
            if final_add: await member.add_roles(*final_add, reason="Role self-management")
            if final_remove: await member.remove_roles(*final_remove, reason="Role self-management")
            await interaction.response.send_message("You roles has been changed!", ephemeral=True) #TODO language pack
        except discord.Forbidden:
            await interaction.response.send_message("Error: I do not have privileges to change Your roles.", ephemeral=True)

class RolePanelView(View):
    def __init__(self, bot, user_roles, selectable_roles_data):
        super().__init__(timeout=300)
        self.add_item(RoleSelectMenu(bot, user_roles, selectable_roles_data))

# --- Main Cog ---

class RoleManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = self.bot.config["database_path"]

    @app_commands.command(name="role", description="Opens panel for role self-management") #TODO language pack
    async def roles(self,interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can be used only on server", ephemeral=True) #TODO language pack
            return
        
        await interaction.response.defer(ephemeral=True, thinking=True)

        member = interaction.user

        if not isinstance(member, discord.Member):
            member = interaction.guild.get_member(member.id)
            if not member:
                await interaction.followup.send("Couldn't download your data from this server.", ephemeral=True) #TODO language pack
                return
            
        member_role_ids = {role.id for role in member.roles}

        all_selectable_roles = [] 
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row # allows access to colums per name
                # Crucial SQL Logic

                placeholders = ', '.join('?' for _ in member_role_ids) # Creating placeholders for each user role

                params = [interaction.guild.id] + list(member_role_ids) #Preparing values to add into query, first is quild_id other is roles IDs

                query = f"""
                    SELECT sr.role_id, sr.role_description
                    FROM selectable_roles sr
                    JOIN role_group_permissions rgp ON sr.group_id = rgp.group_id
                    WHERE sr.guild_id = ? AND rgp.required_role_id IN ({placeholders})
                """

                cursor = await db.execute(query, params)
                all_selectable_roles = await cursor.fetchall()

                unique_roles = {row['role_id']: row for row in all_selectable_roles} #Removing duplicates if user has acces to role from different groups(ex. VIP and moderator has same roles in groups)
                all_selectable_roles = list(unique_roles.values())
        except Exception as e:
            print(f"Error(RoleManager): Exception during downloading roles to be chosen from database: {e}")
            await interaction.followup.send("There occured error during downloading available roles", ephemeral=True)
            return
        if not all_selectable_roles:
            await interaction.followup.send("You dont have acces to any roles to be chosen or no roles has been configured on this server", ephemeral=True)
            return
        
        view = RolePanelView(self.bot, member.roles, all_selectable_roles)
        await interaction.followup.send("Select roles from below list:", view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RoleManager(bot))