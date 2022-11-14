from .onjoin import OnJoin


async def setup(bot, saver):
    data = saver.get()
    await bot.add_cog(OnJoin(bot, saver, data))
    return data
