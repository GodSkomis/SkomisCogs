from redbot.core import commands, checks
from discord.utils import get
from redbot.core import data_manager
import json
from pprint import pprint

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
    #     guild_id: {
    #         channel_id: {
    #             "category": category_id,
    #             "suffix": channel_suffix
    #         }
    #     }
    # }
    data = {}

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
        Saver.save(self.data)
        return 'Channel added successfully'

    def remove_channel(self, guild_id, channel_id):
        try:
            self.data[guild_id].pop(channel_id)
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
    @checks.guildowner()
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
                await ctx.channel.send(self.Listener.remove_channel(str(ctx.guild.id), channel_id))

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
        data_path = str(data_manager.cog_data_path(self)) + "/" + SAVE_FILE_NAME + ".json"
        Saver.data_path = data_path
        data = Saver.read()
        self.Listener.data = data
        flag_to_write = False
        for guild in self.bot.guilds:
            if str(guild.id) not in self.Listener.data:
                self.Listener.data[str(guild.id)] = {}
                flag_to_write = True
        if flag_to_write:
            data = self.Listener.data
            Saver.save(data)
        pprint("Loaded autoroom data:")
        pprint(data)
