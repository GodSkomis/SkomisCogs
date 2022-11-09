from discord import ui
from discord import ButtonStyle, TextStyle
from .Player import Player

player = Player()


class SongModal(ui.Modal, title='URL Input'):
    is_playlist = False
    url = ui.TextInput(label='Enter Youtube URL', style=TextStyle.short, placeholder='https:///youtube.com/',
                       required=True)

    async def on_submit(self, interaction):
        await player.play(interaction, raw_url=str(self.url), is_playlist=self.is_playlist)


class PlaylistModal(SongModal):
    is_playlist = True


class MusicPlayerView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='Play', emoji='⏯️', style=ButtonStyle.green)
    async def play_button(self, interaction, incoming_button):
        guild_id = str(interaction.guild_id)
        await player.resume(guild_id)
        await interaction.response.edit_message(view=self)

    @ui.button(label='Pause', emoji='⏸️', style=ButtonStyle.gray)
    async def pause_button(self, interaction, incoming_button):
        guild_id = str(interaction.guild_id)
        player.pause(guild_id)
        await interaction.response.edit_message(view=self)

    @ui.button(label='Next', emoji='⏭️', style=ButtonStyle.blurple)
    async def next_button(self, interaction, incoming_button):
        guild_id = str(interaction.guild_id)
        await player._play_next(guild_id)
        await player.update_queue_message(guild_id)
        await interaction.response.defer()

    @ui.button(label='Stop', emoji='⏹️', style=ButtonStyle.red)
    async def stop_button(self, interaction, incoming_button):
        guild_id = str(interaction.guild_id)
        await player.stop(guild_id)
        await interaction.response.defer()

    # @ui.button(label='Playlist', emoji='📓', style=ButtonStyle.blurple)
    # async def list_button(self, interaction, incoming_button):
    #     guild_id = str(interaction.guild_id)
    #     await player.update_queue_message(guild_id)
    #     await interaction.response.defer()


class AddSongView(ui.View):
    @ui.button(label='Add song', style=ButtonStyle.grey)
    async def add_song_button(self, interaction, incoming_button):
        await interaction.response.send_modal(SongModal())

    @ui.button(label='Add playlist', style=ButtonStyle.grey)
    async def add_playlist_button(self, interaction, incoming_button):
        await interaction.response.send_modal(PlaylistModal())
