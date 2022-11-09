import asyncio
from pprint import pprint

from discord import FFmpegPCMAudio, ClientException
from .youtubeDriver import find_song, find_playlist
from .utils import _send_error_msg
from discord.utils import get

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn -b:a 128000'}


class Player:
    Player = None

    def __new__(cls, *args, **kwargs):
        if not cls.Player:
            cls.Player = super().__new__(cls)

        return cls.Player

    def __init__(self, bot=None):
        self.bot = bot
        self.remaining_playlist = {}
        self.general_playlist = {}
        self.player_message = {}

    def voice_client(self, guild_id):
        return get(self.bot.guilds, id=int(guild_id)).voice_client

    def is_playing(self, guild_id):
        if vc := self.voice_client(guild_id):
            return vc.is_playing()
        return False

    def queue(self, guild_id):
        i = 1
        response = ""
        if general_playlist := self.Player.general_playlist.get(guild_id):
            for song in general_playlist:
                response += f"*№{i} - {song['title']}*\n"
                i += 1

        if remaining_playlist := self.Player.remaining_playlist.get(guild_id):
            # i = len(general_playlist) + 1
            response += f"**№{i}** - **{remaining_playlist[0]['title']}**\n"
            for k in range(1, len(remaining_playlist)):
                song = remaining_playlist[k]
                response += f"№{k + i} - {song['title']}\n"
        if not response:
            response = "Playlist are empty"
        return response

    async def update_queue_message(self, guild_id, message=None):
        if msg := self.player_message.get(guild_id):
            if not message:
                message = self.queue(guild_id)
            self.player_message[guild_id] = await msg.edit(content=message)

    async def reset(self, guild_id):
        self.remaining_playlist[guild_id] = []
        self.general_playlist[guild_id] = []
        await self.update_queue_message(guild_id)

    def pause(self, guild_id):
        voice_client = self.voice_client(guild_id)
        if voice_client:
            if voice_client.is_playing():
                voice_client.pause()
                return True
        return False

    async def resume(self, guild_id):
        voice_client = self.voice_client(guild_id)
        if voice_client:
            if (not voice_client.is_playing()) and self.remaining_playlist.get(guild_id):
                voice_client.resume()
                await self.update_queue_message(guild_id)
                return True
        return False

    async def _play_next(self, guild_id):
        if self.remaining_playlist.get(guild_id):
            try:
                next_song = self.remaining_playlist[guild_id].pop(0)
                if not self.general_playlist.get(guild_id):
                    self.general_playlist[guild_id] = []
                self.general_playlist[guild_id].append(next_song)
                await self.play_next(guild_id)
            except IndexError:
                await self.stop(guild_id)
        else:
            self.pause(guild_id)

    async def play_next(self, guild_id):
        voice_client = self.voice_client(guild_id)
        if voice_client:
            if voice_client.is_playing():
                voice_client.pause()
            song = self.remaining_playlist[guild_id][0]
            voice_client.play(FFmpegPCMAudio(song['source'], **FFMPEG_OPTIONS),
                              after=lambda e: self.bot.loop.create_task(self._play_next(guild_id)))
            voice_client.pause()
            await self.update_queue_message(guild_id)
            await asyncio.sleep(1)
            voice_client.resume()

        else:
            await self.update_queue_message(guild_id, message="Bot isn't connected")

    async def _check_voice(self, ctx):
        voice = ctx.user.voice
        if voice:
            return voice
        await self.update_queue_message(ctx.guild.id, message="Join to voice channel and then summon me")

    def _handle_song(self, song_info, guild_id):
        song_titles = f"{str(song_info.get('artist'))} - {str(song_info.get('title'))}"
        source_url = song_info['url']
        if not self.remaining_playlist.get(guild_id):
            self.remaining_playlist[guild_id] = []
        self.remaining_playlist[guild_id].append({
            'title': song_titles,
            'source': source_url
        })

    async def stop(self, guild_id):
        if vc := self.voice_client(guild_id):
            vc.stop()
            await vc.disconnect()
            await self.reset(guild_id)

    async def play(self, ctx, raw_url: str, is_playlist=False):
        user_voice = await self._check_voice(ctx)
        if not user_voice or raw_url.isdigit():
            await _send_error_msg(ctx)
        guild_id = str(ctx.guild.id)
        await self.update_queue_message(guild_id, message='Download started')
        await ctx.response.defer()
        if is_playlist:
            song_info = find_playlist(raw_url)
            if not song_info:
                await _send_error_msg(ctx)
            for song in song_info:
                self._handle_song(song, guild_id)
        else:
            url = raw_url.split('&')[0]
            song_info = find_song(url)
            if not song_info:
                await _send_error_msg(ctx)
            self._handle_song(song_info, guild_id)
        await self.update_queue_message(guild_id, message=self.queue(guild_id))
        if not self.voice_client(guild_id):
            try:
                await user_voice.channel.connect()
            except ClientException:
                pass

        if not self.is_playing(guild_id):
            await self.play_next(guild_id)
