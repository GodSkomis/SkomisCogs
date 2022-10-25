from youtube_dl import YoutubeDL

YOUTUBE_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}


async def find_song(url):
    with YoutubeDL(YOUTUBE_OPTIONS) as y:
        info = y.extract_info("ytsearch:%s" % url, download=False)['entries'][0]
        return info
