from discord.ext import commands
from discord.utils import get
from pprint import pprint


HELP_MESSAGE = """
    - add channel_id category_id (optional) suffix
    - remove channel_id
"""


def is_guild_owner(ctx):
    return ctx.author.id == ctx.guild.owner_id


class ChannelListener:
    data = {}

    def __init__(self, saver):
        self.Saver = saver

    def add_channel(self, guild_id, channel_id: str, category_id, channel_suffix):
        if channel_id in self.data[str(guild_id)]:
            return "This channel already used"
        if not channel_suffix:
            channel_suffix = 'room'
        channel_data = {
            "category": category_id,
            "suffix": channel_suffix
        }
        guild_data = self.data[guild_id]
        guild_data[channel_id] = channel_data
        self.Saver.insert(self.data)
        return 'Channel added successfully'

    def remove_channel(self, guild_id, channel_id):
        try:
            self.data[guild_id].pop(channel_id)
            # self.Saver.delete(channel_id)
            self.Saver.insert(self.data)
        except KeyError:
            return "This channel aren't in use"
        else:
            return "Channel removed successfully"


class Autoroom(commands.Cog):
    def __init__(self, bot, saver):
        self.bot = bot
        self.Saver = saver.Autoroom
        self.Listener = ChannelListener(saver.Autoroom)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        for channel_id in (x := self.Listener.data[str(member.guild.id)]):
            category = get(member.guild.categories, id=int(x[channel_id]['category']))
            if before.channel:
                if (y := before.channel) in category.channels:
                    if len(y.members) == 0:
                        await y.delete()
                    if not after.channel:
                        break

            if after.channel and (not member.bot):
                if after.channel.id == int(channel_id):
                    new_channel_name = f"{member.nick if member.nick else member.name}`s {x[channel_id]['suffix']}"
                    guild = member.guild
                    new_channel = await guild.create_voice_channel(new_channel_name, category=category,
                                                                   bitrate=guild.bitrate_limit)
                    await new_channel.edit(reason=None, position=0)
                    await member.move_to(new_channel)
                    if not before.channel:
                        break

    @commands.command()
    # @commands.check(is_guild_owner)
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
                    response = self.Listener.add_channel(str(ctx.guild.id), channel_id, category_id,
                                                         new_channel_suffix)
                    await ctx.channel.send(f"{response}")

            elif index == 'remove':
                channel_id = args[0]
                await ctx.channel.send(self.Listener.remove_channel(str(ctx.guild.id), str(channel_id)))

            elif index == 'list':
                response = {}
                _DATA = self.Listener.data.get(str(ctx.guild.id))
                if not _DATA:
                    await ctx.channel.send("List are empty")
                    return 0

                for channel_id in _DATA:
                    channel_name = (get(ctx.guild.channels, id=int(channel_id))).name
                    category_name = (get(ctx.guild.categories, id=int(_DATA[channel_id]['category']))).name
                    response[channel_name] = int(channel_id)
                    response[category_name] = int(_DATA[channel_id]['category'])

                await ctx.channel.send(f"{self.Listener.data[str(ctx.guild.id)]}")

                await ctx.channel.send(f"{response}")

            else:
                await ctx.channel.send(HELP_MESSAGE)

        except Exception as ex:
            pprint(ex)
            await ctx.channel.send('Unexpected error, check incoming data and try again')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if (ID := str(guild.id)) not in (DATA := self.Listener.data):
            DATA[ID] = []

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if (ID := str(guild.id)) in (DATA := self.Listener.data):
            DATA.pop(ID)

    @commands.Cog.listener()
    async def on_ready(self):
        data = self.Saver.getAll()
        self.Listener.data = data
        print("Loaded Autoroom data:")
        pprint(data)
