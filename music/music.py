from discord import ClientException
from .youtubeDriver import find_song, find_playlist
from redbot.core import commands
import discord

INVALID_URL_ERROR_MESSAGE = "Invalid URL"
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn -b:a 128000'}


async def _send_error_msg(ctx):
    ctx.channel.send(INVALID_URL_ERROR_MESSAGE)

async def _send_big_message(ctx, response):
    message = response
    for i in range(message//2000):
        await ctx.channel.send(message[:2000])
        message = message[2000:]
    await ctx.channel.send(message)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.remaining_playlist = []
        self.general_playlist = []
        self.is_playing = False
        self.voice_channel = None

    def _get_voice_client(self):
        if self.voice_channel:
            return self.voice_channel.guild.voice_client

    def reset(self):
        self.voice_channel = None
        self.is_playing = False
        self.remaining_playlist = []
        self.general_playlist = []

    def get_voice_client(self):
        voice_client = self.voice_channel.guild.voice_client
        return voice_client

    def _stop_voice_client(self):
        voice_client = self._get_voice_client()
        if voice_client.is_playing:
            voice_client.stop()

    async def _resume(self, ctx):
        if (not self.is_playing) and self.remaining_playlist:
            self.is_playing = True
            await ctx.channel.send(f"Now is playing:\n{self.remaining_playlist[0]['title']}")
            self.voice_channel.guild.voice_client.resume()

    def _play_next(self, slice_numbers=1):
        if self.remaining_playlist:
            for i in range(slice_numbers):
                try:
                    self.general_playlist.append(self.remaining_playlist.pop(0))
                except IndexError:
                    break
            self.play_next()

    def play_next(self):
        if self.remaining_playlist:
            voice_client = self._get_voice_client()
            if voice_client.is_playing():
                voice_client.pause()
            song = self.remaining_playlist[0]
            self.voice_channel.guild.voice_client.play(discord.FFmpegPCMAudio(song['source'], **FFMPEG_OPTIONS),
                                                       after=lambda e: self._play_next())
        else:
            self.is_playing = False
            self._stop_voice_client()

    async def start_play(self):
        self.is_playing = True
        self.play_next()

    @staticmethod
    async def _check_voice(ctx):
        voice = ctx.author.voice
        if not voice:
            await ctx.channel.send("Join to voice channel and then summon me")
        return voice

    def _handle_song(self, song_info):
        song_titles = str(song_info.get('artist')) + ' - ' + str(song_info.get('title'))
        source = song_info['formats'][0]['url']
        self.remaining_playlist.append({
            'title': song_titles,
            'source': source
        })
        len1 = len(self.remaining_playlist)
        len2 = len(self.general_playlist)
        response = f"***{song_titles}*** | *track* **№{len1 + len2}** *in playlist*\n"
        return response

    async def play(self, ctx, raw_url: str, is_playlist=False):
        voice = await self._check_voice(ctx)
        if not voice or raw_url.isdigit():
            return
        voice_channel = voice.channel
        response = ''
        if is_playlist:
            song_info = find_playlist(raw_url)
            if not song_info:
                await _send_error_msg(ctx)
            for song in song_info:
                response += self._handle_song(song)
        else:
            url = raw_url.split('&')[0]
            song_info = find_song(url)
            if not song_info:
                await _send_error_msg(ctx)
            response = self._handle_song(song_info)

        await ctx.channel.send(response)
        await ctx.message.delete()

        if not self.voice_channel:
            try:
                self.voice_channel = voice_channel
                await voice_channel.connect()
            except ClientException:
                return
        voice_client = self.get_voice_client()
        if voice_client:
            if not voice_client.is_playing():
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
    async def music(self, ctx, index=None, arg1=None, arg2=None):
        if index == 'play' or 'add':
            if arg1 == 'playlist' and arg2:
                await self.play(ctx, arg2, is_playlist=True)
            elif arg1:
                await self.play(ctx, arg1)
            else:
                await self._resume(ctx)

        if index == 'pause':
            if self.is_playing:
                self.voice_channel.guild.voice_client.pause()
                self.is_playing = False
                response = "Silence!"
            else:
                response = "I'm not playing now"
            await ctx.channel.send(response)

        if index == 'resume':
            await self._resume(ctx)

        if index == 'stop':
            voice_client = self.voice_channel.guild.voice_client
            voice_client.stop()
            await voice_client.disconnect()
            self.reset()

        if index == 'skip' or index == 'next':
            if self.remaining_playlist:
                slice_numbers = int(arg1) if str(arg1).isdigit() else 1
                self._play_next(slice_numbers)
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
            if self.general_playlist:
                for song in self.general_playlist:
                    i += 1
                    response += f"*№{i} - {song['title']}*\n"
            if self.remaining_playlist:
                i = len(self.general_playlist) + 1
                response += f"**№{i}** - **{self.remaining_playlist[0]['title']}**\n"
                for k in range(1, len(self.remaining_playlist)):
                    song = self.remaining_playlist[k]
                    response += f"№{k + i} - {song['title']}\n"
            if not response:
                response = "Playlist are empty"

            await _send_big_message(ctx, response)
