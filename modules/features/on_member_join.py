import discord
from discord.ext import commands

## for future private messages to select roles onm server
class RoleAssignmentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) #timeout=None makes that message will not dissapear

        """
        === Placeholder for future buttons ===
        self.add_item(discord.ui.Button)(label="I want role A!"), custom_id="role_a_button)) #TODO language pack
        self.add_item(discord.ui.Button)(label="I want role B!"), custom_id="role_b_button))
        ======================================
        """

class WelcomeHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        ### This maintains new member join events
        
        #1. Sending private message with panel
        try:
            dm_channel = await member.create_dm()

            view = RoleAssignmentView() #we creating instance for our panel

            welcome_text = f"Hej {member.name}, witaj w cyrku! Honk! \n Poniżej możesz wybrać swoje role" #TODO  language pack /// this is a welcome message

            await dm_channel.send(welcome_text, view=view) #we are sending welcome with role changing panel

        except discord.errors.Forbidden:
            print (f"Cannot send message to {member.name} (ID: {member.id}).") #TODO language pack // There are no privileges to send direct messages or they are blocked by user
        except Exception as e:
            print (f"There occured unexpected error while trying to send DM to {member.name}: {e}") #TODO language pack

        #2. Sending notification to public channel
        # we are also setting up an channel ID from config that has been setted during bot initialization, we are using .get() for safety, if there is no key in config
        notification_channel_id = self.bot.config.get("bot_settings", {}).get("notification_channel_id")

        if not notification_channel_id:
            print("Warning! Not found 'notification_channel_id' in config.json in section 'bot_settings.") #TODO language pack
            return
        
        channel = self.bot.get_channel(notification_channel_id)
        if channel and isinstance(channel, discord.TextChannel):
            try:
                await channel.send("Nowy użytkownik dołączył do serwera: {member.mention}! Witamy! Honk!") #TODO language pack
            except discord.errors.Forbidden:
                print(f"ERROR: No privileges to send messages in notification channel (ID: {notification_channel_id})") #TODO languge pack
        else:
            print(f"ERROR! Notification channel not found, ID: {notification_channel_id}")


async def setup(bot: commands.Bot): #standard initialization function
    await bot.add_cog(WelcomeHandler(bot))