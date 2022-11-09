from .music import Music


async def setup(bot, saver):
    await bot.add_cog(Music(bot, saver))
