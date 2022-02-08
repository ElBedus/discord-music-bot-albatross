from config import config
import discord
from discord.ext import commands

from time import time


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ======================================= #

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def ping(self, ctx):
        try:
            start_time = time()
            message = await ctx.send(".")
            end_time = time()
            tmp1 = round(self.bot.latency * 1000)
            tmp2 = round((end_time - start_time) * 1000)
            await ctx.send(embed = discord.Embed(title =f"Ping: **{tmp1}**ms\nAPI: **{tmp2}**ms", color=config['color']['system']))
            await message.delete()
            return
        except:
            await ctx.send(embed = discord.Embed(description = "**__Неизвестная ошибка__**", color=config['color']['red']))


def setup(bot):
    bot.add_cog(Admin(bot))
