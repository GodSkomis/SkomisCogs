from .autoroom import Autoroom


async def setup(bot, Saver):
    await bot.add_cog(Autoroom(bot, Saver))
