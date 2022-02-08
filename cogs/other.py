from config import config
import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext


class Other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ======================================= #

    @commands.command()
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def help(self, ctx):
        p=config['bot']['prefix']
        msg = (
            f"\n\n**{p}play** `[YT-url / Spotify-url / название]` ({p}p) - Поставить трек в очередь"
            f"\n**{p}radio** `[Жанр/поиск]` - Вкл/выкл радио"
            f"\n**{p}skip** ({p}s) - Пропустить трек"
            f"\n**{p}queue** ({p}q) - Показать очередь воспроизведения"
            f"\n**{p}pause** ({p}resume) - Вкл/выкл паузы"
            f"\n**{p}clear** - Очищение всей очереди воспроизведения"
            f"\n**{p}remove** `[№]` ({p}r) - Удаляет из очереди трек с указанным номером"
            f"\n**{p}loop** - Вкл/выкл повтора"
            f"\n**{p}loop_all** - Вкл/выкл повтора всей очереди"
            f"\n**{p}join** - Призвать бота"
            f"\n**{p}leave** - Выгнать бота"

            f"\n\n**{p}help** - Список команд бота"
            f"\n**{p}radio_info** ({p}ri) - Информация про работу радио"
            f"\n**{p}change_log** ({p}log)- Список обновлений бота"
            f"\n```● У бота есть аналогичные slash-команды\n● Не используйте бота в каналах-трибунах!```"
        )
        await ctx.send(embed = discord.Embed(title = "**__Список команд:__**", description = msg, color=config['color']['main']))

    # ======================================= #

    @cog_ext.cog_slash(name = 'help', description = 'Список команд бота', options = [], guild_ids=None)
    async def help_slash(self, ctx: SlashContext):
        await self.help(ctx)



def setup(bot):
    bot.add_cog(Other(bot))
