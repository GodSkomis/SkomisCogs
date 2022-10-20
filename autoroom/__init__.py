from .autoroom import Autoroom


def setup(bot):
    bot.add_cog(Autoroom(bot))
