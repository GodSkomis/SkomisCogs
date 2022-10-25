from discord import ClientException

from .youtubeDriver import find_song
from redbot.core import commands
import discord
from pprint import pprint

INVALID_URL_ERROR_MESSAGE = "Invalid URL"
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn'}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playlist = []
        self.is_playing = False
        self.voice_channel = None

    def reset(self):
        self.voice_channel = None
        self.is_playing = False
        self.playlist = []

    def _play_next(self, slice_numbers=1):
        if self.playlist:
            self.playlist = self.playlist[int(slice_numbers):]
            self.play_next()

    def play_next(self):
        if self.playlist:
            song = self.playlist[0]
            self.voice_channel.guild.voice_client.play(discord.FFmpegPCMAudio(song['source'], **FFMPEG_OPTIONS),
                                                       after=lambda e: self._play_next())
        else:
            self.is_playing = False

    async def start_play(self):
        self.is_playing = True
        self.play_next()

    def _get_voice_client(self):
        if self.voice_channel:
            return self.voice_channel.guild.voice_client

    @staticmethod
    async def _check_voice(ctx):
        voice = ctx.author.voice
        if not voice:
            await ctx.channel.send("Connect to voice channel first")
        return voice

    async def play(self, ctx, raw_url):
        voice = await self._check_voice(ctx)
        if not voice:
            return

        voice_channel = voice.channel
        url = raw_url.split('&')

        song_info = await find_song(url[0])

        if not song_info:
            ctx.channel.send(INVALID_URL_ERROR_MESSAGE)
            return
        if len(url) > 1:
            await ctx.channel.send("I inform you, i added song to queue but, i don't wanna play a "
                                   "playlist for mortal being")

        song_titles = song_info['title']
        if not song_titles:
            song_titles = "NoName"
        source = song_info['formats'][0]['url']
        self.playlist.append({
            'title': song_titles,
            'source': source
        })

        await ctx.channel.send(f"{song_titles} track #{len(self.playlist)} in playlist")

        if not self.voice_channel:
            try:
                self.voice_channel = voice_channel
                await voice_channel.connect()
            except ClientException:
                return
            await self.start_play()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and self.voice_channel:
            if len(self.voice_channel.members) == 1:
                voice_client = self._get_voice_client()
                voice_client.stop()
                await voice_client.disconnect()
                self.reset()

    @commands.command()
    async def music(self, ctx, index=None, arg1=None):
        if index == 'play':
            if arg1:
                await self.play(ctx, arg1)
        if index == 'pause':
            if self.is_playing:
                self.voice_channel.guild.voice_client.pause()
                self.is_playing = False
                response = "Silence!"
            else:
                response = "I'm not playing now"
            await ctx.channel.send(response)
        if index == 'resume':
            if (not self.is_playing) and self.playlist:
                self.is_playing = True
                await ctx.channel.send(f"Now is playin: {self.playlist[0]['title']}")
                self.voice_channel.guild.voice_client.resume()
        if index == 'stop':
            voice_client = self.voice_channel.guild.voice_client
            voice_client.stop()
            await voice_client.disconnect()
            self.reset()
        if index == 'skip' or index == 'next':
            if self.playlist:
                skip_nuber = int(arg1) if str(arg1).isdigit() else 1
                voice_client = self._get_voice_client()
                voice_client.stop()
                self._play_next(skip_nuber)
            else:
                if self.voice_channel:
                    voice_client = self._get_voice_client()
                    await voice_client.disconnect()
                    self.reset()
                    await ctx.channel.send("**Playlist end**, see you insect")
                else:
                    await ctx.channel.send("Summon me first insect")
        if index == 'queue' or index == 'list':
            i = 0
            response = ""
            for song in self.playlist:
                i += 1
                response += f"#{i} - {song['title']}"
            await ctx.channel.send(response)
        # if index == 'follow' or index == 'move':
        #     new_voice = await self._check_voice(ctx)
        #     if new_voice:
        #         if new_voice.channel == self.voice_channel:
        #             await ctx.channel.send("Im here already")
        #         voice_client = self._get_voice_client()
        #         voice_client.pause()
        #         await voice_client.disconnect()
        #         await new_voice.channel.connect()
        #         self.voice_channel = new_voice.channel
        #         voice_client.resume()
