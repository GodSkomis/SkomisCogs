from .autoroom import Autoroom, Saver
import os


async def setup(bot):
    if not os.path.exists(Saver.data_path):
        dir_path = Saver.data_path.split(Saver.SAVE_FILE_NAME)[0]
        os.mkdir(dir_path)
        print(f'Created directory {dir_path}')
    if not os.path.isfile(Saver.data_path):
        Saver.save({})
    await bot.add_cog(Autoroom(bot))
