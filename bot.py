from config import config
from utils.load_cogs import load_cogs
import discord
from discord.ext import commands
from discord_slash import SlashCommand

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config['bot']['prefix'], help_command=None, intents=intents)
slash = SlashCommand(bot, sync_commands = True, sync_on_cog_reload=True)

# ======================================= #


@bot.event
async def on_ready():
    await bot.cogs['Music'].init_func()

    p=config['bot']['prefix']
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(f"{p}help - список команд"))
    print("[i] " + config["bot"]["name"] + " готов к работе!\n")

@bot.event
async def on_message(ctx, *args):
    ctx.content = ctx.content.replace('’', '')
    await bot.process_commands(ctx, *args)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        s=round(error.retry_after, 1)
        await ctx.reply(content=f"Подождите **__{s}__**с. перед тем как использовать команду еще раз.")
    else:
        p=config['bot']['prefix']
        await ctx.send(embed = discord.Embed(description = f"Команда не распознана. Используйте **__{p}help__** или проверьте синтаксис.", color=config['color']['red']))
    print("[-] "+str(error))

@bot.event
async def on_guild_join(guild):
    print("[i] new guild:", guild)
    await bot.cogs['Music'].init_new_guild(guild)


# ======================================= #

load_cogs(bot)
bot.run(config['bot']['token'])
