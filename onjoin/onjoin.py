from discord.ext import commands
from discord.utils import get

from Saver.Saver import FileObject


def is_owner(ctx):
    if ctx.author.id == ctx.guild.owner_id:
        return True
    return False


class OnJoin(commands.Cog):

    def __init__(self, bot, saver: FileObject, init_data=None):
        self.bot = bot
        self.saver = saver
        if init_data:
            self.roles = init_data
        else:
            self.roles = {}

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role_id = self.roles.get(str(member.guild.id))
        if role_id:
            role = get(member.guild.roles, id=role_id)
            await member.add_roles(role, reason='Auto role on join')

    @commands.command()
    @commands.check(is_owner)
    async def onjoin(self, ctx, index, role_id=None):
        if index == 'add':
            if role_id:
                await self.add_role(ctx, role_id)
            else:
                await ctx.send("Add role ID to command")
        elif index == 'remove':
            await self.remove_role(ctx)
        elif index == 'list' or index == 'status':
            await self.get_role_list(ctx)

    async def add_role(self, ctx, role_id):
        role_id = int(role_id)
        role = get(ctx.guild.roles, id=role_id)
        if not role:
            await ctx.send(f"{role_id} is wrong role ID")
            return
        guild_id = str(ctx.guild.id)
        self.roles[guild_id] = role_id
        self.saver.insert({guild_id: role_id})
        await ctx.send(f"{role.name} was added successful")

    async def remove_role(self, ctx):
        guild_id = str(ctx.guild.id)
        if not (guild_id in self.roles):
            await ctx.send("Nothing to delete")
            return

        role_id = self.roles.pop(guild_id)[guild_id]
        self.saver.delete(str(ctx.guild.id))
        await ctx.send(
            f"{get(ctx.guild.roles, id=role_id).name} was removed successful")

    async def get_role_list(self, ctx):
        await ctx.send(get(ctx.guild.roles, id=self.saver.get(str(ctx.guild.id))))


