from redbot.core import commands
from discord.utils import get
from redbot.core import data_manager
import json

HELP_MESSAGE = """
    - add channel_id category_id (optional) suffix
    - remove channel_id
"""

SAVE_FILE_NAME = "AutoroomData"


class Saver:
    data_path = ''

    @classmethod
    def save(cls, data):
        if cls.data_path:
            with open(cls.data_path, 'w') as f:
                json.dump(data, f)

    @classmethod
    def read(cls):
        if cls.data_path:
            try:
                with open(cls.data_path, 'r') as f:
                    data = json.load(f)
                    return data
            except json.JSONDecodeError:
                return {}
            except FileNotFoundError:
                cls.save({})
                return cls.read()


class ChannelListener:
    # data = {
    # channel_id: {
    # "channel": channel_name,
    # "category": category_name,
    # "table_prefix": table_prefix
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
        Saver.save(self.data)
        return 'Channel added successfully'

    def remove_channel(self, channel_id):
        try:
            self.data.pop(channel_id)
            Saver.save(self.data)
        except KeyError:
            return "This channel aren't in use"
        else:
            return "Channel removed successfully"


class Autoroom(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.Listener = ChannelListener()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        for channel_id in (x := self.Listener.data):
            category = get(member.guild.categories, name=x[channel_id]['category'])
            if before.channel:
                if (y := before.channel) in category.channels:
                    if len(y.members) == 0:
                        await y.delete()
                    if not after.channel:
                        break

            if after.channel:
                if after.channel.name == x[channel_id]['channel']:
                    new_channel_name = f"{member.nick if member.nick else member.name}`s {x[channel_id]['suffix']}"
                    new_channel = await member.guild.create_voice_channel(new_channel_name, category=category)
                    await new_channel.edit(reason=None, position=0)
                    await member.move_to(new_channel)
                    if not before.channel:
                        break

    @commands.command()
    @commands.is_owner()
    async def autoroom(self, ctx, index, *args):
        try:
            channel_id = args[0]
            if index == 'add':
                category_id = args[1]
                channel = get(ctx.guild.channels, id=int(channel_id))
                category = get(ctx.guild.categories, id=int(category_id))
                if not channel:
                    await ctx.channel.send("Channel name error")
                elif not category:
                    await ctx.channel.send("Category name error")
                else:
                    new_channel_suffix = ' '.join(str(x) for x in args[2:]) if len(args) > 2 else None
                    response = self.Listener.add_channel(channel_id, channel.name, category.name, new_channel_suffix)
                    await ctx.channel.send(f"{response}")

            elif index == 'remove':
                await ctx.channel.send(self.Listener.remove_channel(channel_id))

            elif index == 'list':
                await ctx.channel.send(f"{self.Listener.data}")

            else:
                await ctx.channel.send(HELP_MESSAGE)

        except Exception as ex:
            print(ex)
            await ctx.channel.send('Unexpected error, check incoming data and try again')

    @commands.Cog.listener()
    async def on_ready(self):
        data_path = str(data_manager.cog_data_path(self)) + "/" + SAVE_FILE_NAME + ".json"
        Saver.data_path = data_path
        data = Saver.read()
        self.Listener.data = data
        print("Loaded autoroom data:")
        print(data)
