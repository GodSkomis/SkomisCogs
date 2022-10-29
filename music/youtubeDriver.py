from youtube_dl import YoutubeDL

SONG_YOUTUBE_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}
PLAYLIST_YOUTUBE_OPTIONS = {'format': 'bestaudio'}


def find_song(url):
    with YoutubeDL(SONG_YOUTUBE_OPTIONS) as y:
        info = y.extract_info("ytsearch:%s" % url, download=False)
        return info['entries'][0]


def find_playlist(url):
    with YoutubeDL(PLAYLIST_YOUTUBE_OPTIONS) as y:
        info = y.extract_info(url, download=False)
        return info['entries']
