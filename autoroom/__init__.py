from .autoroom import Autoroom


async def setup(bot, saver):
    await bot.add_cog(Autoroom(bot, saver))
