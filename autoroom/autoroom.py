from redbot.core import commands
from discord.utils import get

HELP_MESSAGE = """
    - add channel_name category_name
    - remove channel_name
"""


class Saver:
    pass


class ChannelListener:

    # data = {
    # channel_id: {
    # "channel": channel_name,
    # "category": category_name,
    # "table_prefix": table_prefix
    # 'room_count': room_count
    # }
    # }
    data = {}

    def add_channel(self, channel_name, channel, category, channel_suffix):
        if channel_name in self.data:
            return "This channel already used"
        if not channel_suffix:
            channel_suffix = 'room'
        channel_data = {
            'channel': channel,
            'category': category,
            'suffix': channel_suffix
        }
        self.data[channel_name] = channel_data
        return 'Successful added channel to listener'

    # def remove_channel(self, channel):
    #     self.channels.remove(channel)

    def reset_channels(self):
        self.data = {}


Listener = ChannelListener()


class Autoroom(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        for channel_id in (x := ChannelListener.data):
            category = get(member.guild.categories, name=x[channel_id]['category'])
            if before.channel:
                if (y := before.channel) in category.channels:
                    if len(y.members) == 0:
                        await y.delete()

            if after.channel:
                if after.channel.name == x[channel_id]['channel']:
                    new_channel_name = f"{member.nick if member.nick else member.name}`s {x[channel_id]['suffix']}"
                    new_channel = await member.guild.create_voice_channel(new_channel_name, category=category)
                    await new_channel.edit(reason=None, position=0)
                    await member.move_to(new_channel)

    @commands.command()
    @commands.is_owner()
    async def autoroom(self, ctx, index, *args):
        try:
            if index == 'add':
                channel_id = args[0]
                category_id = args[1]
                channel = get(ctx.guild.channels, id=int(channel_id))
                category = get(ctx.guild.categories, id=int(category_id))
                if not channel:
                    await ctx.channel.send("Channel name error")
                elif not category:
                    await ctx.channel.send("Category name error")
                else:
                    new_channel_suffix = ' '.join(str(x) for x in args[2:]) if len(args) > 2 else None
                    response = Listener.add_channel(channel_id, channel.name, category.name, new_channel_suffix)
                    await ctx.channel.send(f"{response}")

            elif index == 'list':
                await ctx.channel.send(f"{Listener.data}")

            else:
                await ctx.channel.send(HELP_MESSAGE)

        except Exception as ex:
            print(ex)
            await ctx.channel.send('Unexpected error, check incoming data and try again')