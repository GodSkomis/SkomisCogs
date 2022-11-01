from discord.ext import commands
from .playerViews import MusicPlayerView, AddSongView
from .Player import Player

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn -b:a 128000'}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.Player = Player()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot:
            if vc := self.Player.voice_client:
                if vc.is_connected():
                    if before.channel.id == vc.channel.id and len(before.channel.members) == 1:
                        vc.stop()
                        await vc.disconnect()
                        self.Player.reset()

    @commands.command()
    async def music(self, ctx, index=None, arg1=None, arg2=None):
        messages = []
        async for message in ctx.channel.history():
            messages.append(message)
        await ctx.channel.delete_messages(messages)
        await ctx.send('', view=MusicPlayerView())
        await ctx.send('', view=AddSongView())
        self.Player.list_message = await ctx.send(self.Player.queue)