from discord import FFmpegPCMAudio, ClientException
from .youtubeDriver import find_song, find_playlist
from .utils import _send_error_msg

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn -b:a 128000'}


class Player:
    Player = None

    def __new__(cls, *args, **kwargs):
        if not cls.Player:
            cls.Player = super().__new__(cls)

        return cls.Player

    def __init__(self):
        self.remaining_playlist = []
        self.general_playlist = []
        self.voice_channel = None
        self.list_message = None

    @property
    def voice_client(self):
        return self._get_voice_client()

    @property
    def is_playing(self):
        if not self.voice_client:
            return False
        return self.voice_client.is_playing()

    @property
    def queue(self):
        i = 0
        response = ""
        if general_playlist := self.Player.general_playlist:
            for song in general_playlist:
                i += 1
                response += f"*№{i} - {song['title']}*\n"
        if remaining_playlist := self.Player.remaining_playlist:
            i = len(general_playlist) + 1
            response += f"**№{i}** - **{remaining_playlist[0]['title']}**\n"
            for k in range(1, len(remaining_playlist)):
                song = remaining_playlist[k]
                response += f"№{k + i} - {song['title']}\n"
        if not response:
            response = "Playlist are empty"
        return response

    async def update_queue_message(self):
        if self.list_message:
            await self.list_message.edit(content=self.queue)

    def _get_voice_client(self):
        if self.voice_channel:
            return self.voice_channel.guild.voice_client

    def reset(self):
        self.voice_channel = None
        self.list_message = None
        self.remaining_playlist = []
        self.general_playlist = []

    def get_voice_client(self):
        voice_client = self.voice_channel.guild.voice_client
        return voice_client

    def _stop_voice_client(self):
        if self.is_playing:
            self.voice_client.stop()

    def pause(self):
        if self.is_playing:
            self.voice_client.pause()
            return True
        return False

    def resume(self):
        if (not self.is_playing) and self.remaining_playlist:
            self.voice_client.resume()

    async def _resume(self, ctx):
        if (not self.is_playing) and self.remaining_playlist:
            # await ctx.channel.send(f"Now is playing:\n{self.remaining_playlist[0]['title']}")
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
            self.voice_channel.guild.voice_client.play(FFmpegPCMAudio(song['source'], **FFMPEG_OPTIONS),
                                                       after=lambda e: self._play_next())
        else:
            self._stop_voice_client()

    async def start_play(self):
        self.play_next()

    @staticmethod
    async def _check_voice(ctx):
        voice = ctx.user.voice
        if not voice:
            await ctx.channel.send("Join to voice channel and then summon me")
        return voice

    def _handle_song(self, song_info):
        song_titles = f"{str(song_info.get('artist'))} - {str(song_info.get('title'))}"
        source_url = song_info['url']
        self.remaining_playlist.append({
            'title': song_titles,
            'source': source_url
        })
        len1 = len(self.remaining_playlist)
        len2 = len(self.general_playlist)
        response = f"***{song_titles}*** | *track* **№{len1 + len2}** *in playlist*\n"
        return response

    async def stop(self):
        if self.voice_client:
            self.voice_client.stop()
            await self.voice_client.disconnect()
            self.reset()

    async def play(self, ctx, raw_url: str, is_playlist=False):
        voice = await self._check_voice(ctx)
        if not voice or raw_url.isdigit():
            return
        voice_channel = voice.channel
        response = ''
        await ctx.response.defer()
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

        # await _send_big_message(ctx, response)
        # await ctx.message.delete()
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
        await self.update_queue_message()
