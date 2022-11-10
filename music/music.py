from discord.ext import commands
from .playerViews import MusicPlayerView, AddSongView
from .Player import Player
from pprint import pprint
from discord.utils import get as discord_get

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn -b:a 128000'}


class Music(commands.Cog):
    def __init__(self, bot, saver):
        self.bot = bot
        self.Saver = saver.Music
        self.Player = Player(bot)

    @commands.Cog.listener()
    async def on_ready(self):
        data = self.Saver.get()
        print("Loaded Music Data:")
        pprint(data)
        await self._load_data(data)

    async def _load_data(self, player_data):
        for guild_id in player_data:
            guild = discord_get(self.bot.guilds, id=int(guild_id))
            if guild:
                channel = discord_get(guild.channels, id=int(player_data[guild_id]['channel_id']))
                if channel:
                    await self._music(channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and before.channel:
            guild_id = str(before.channel.guild.id)
            if vc := self.Player.voice_client(guild_id):
                if vc.is_connected():
                    if before.channel.id == vc.channel.id and len(before.channel.members) == 1:
                        await self.Player.stop(guild_id)

    @commands.command()
    async def music(self, ctx):  # index=None, arg1=None, arg2=None
        await self._music(ctx.channel)

    async def _music(self, channel):
        messages = []
        async for message in channel.history():
            messages.append(message)
        await channel.delete_messages(messages)
        await channel.send('', view=MusicPlayerView(self.Player))
        await channel.send('', view=AddSongView(self.Player))
        guild_id = str(channel.guild.id)
        self.Player.player_message[guild_id] = await channel.send(self.Player.queue(guild_id))
        self.Saver.insert({guild_id: {
            'channel_id': str(channel.id)
        }})
