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
            voice_client = self.Player._get_voice_client()
            if voice_client:
                if self.Player.voice_client.is_connected():
                    if before.channel.id == voice_client.channel.id and len(before.channel.members) == 1:
                        voice_client.stop()
                        await voice_client.disconnect()
                        self.Player.reset()

    @commands.command()
    async def music(self, ctx, index=None, arg1=None, arg2=None):
        # if index == 'play' or 'add':
        #     if arg1 == 'playlist' and arg2:
        #         await self.Player.play(ctx, arg2, is_playlist=True)
        #         await ctx.send('', view=MusicPlayer())
        #     elif arg1:
        #         await self.Player.play(ctx, arg1)
        #         await ctx.send('', view=MusicPlayer())
        #     else:
        #         await self.Player._resume(ctx)
        #
        # if index == 'pause':
        #     self.Player.pause()
        #
        # if index == 'resume':
        #     await self.Player._resume(ctx)
        #
        # if index == 'stop':
        #     self.Player.stop()
        #
        # if index == 'skip' or index == 'next':
        #     if self.Player.remaining_playlist:
        #         slice_numbers = int(arg1) if str(arg1).isdigit() else 1
        #         self.Player._play_next(slice_numbers)
        #     else:
        #         if self.Player.voice_channel:
        #             voice_client = self.Player._get_voice_client()
        #             await voice_client.disconnect()
        #             self.Player.reset()
        #             await ctx.channel.send("**Playlist end**, see you insect")
        #         else:
        #             await ctx.channel.send("Summon me first insect")
        #
        # if index == 'queue' or index == 'list':
        #     i = 0
        #     response = ""
        #     if general_playlist := self.Player.general_playlist:
        #         for song in general_playlist:
        #             i += 1
        #             response += f"*№{i} - {song['title']}*\n"
        #     if remaining_playlist := self.Player.remaining_playlist:
        #         i = len(general_playlist) + 1
        #         response += f"**№{i}** - **{remaining_playlist[0]['title']}**\n"
        #         for k in range(1, len(remaining_playlist)):
        #             song = remaining_playlist[k]
        #             response += f"№{k + i} - {song['title']}\n"
        #     if not response:
        #         response = "Playlist are empty"
        #     await _send_big_message(ctx, response)
        #
        # if index == 'test':
        #     await ctx.send('', view=MusicPlayer())
        async for message in ctx.channel.history():
            await message.delete()
        await ctx.send('', view=MusicPlayerView())
        await ctx.send('', view=AddSongView())
        self.Player.list_message = await ctx.send(self.Player.queue)