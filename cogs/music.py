from config import config, YDL_OPTS, FFMPEG_OPTS
import discord
from discord.ext import commands, tasks
from discord.utils import get
from discord_slash import cog_ext, SlashContext

from asyncio import sleep
from time import time

from utils.radio_words import words
from random import choice
from discord import FFmpegPCMAudio
from requests import get as r_get
from youtube_dl import YoutubeDL
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


class Music(commands.Cog):
    def __init__(self, bot):
        self.play_message = {}
        self.no_playing = {}
        self.now_playing = {}
        self._queue = {}
        self._pause = {}
        self._loop = {}
        self.clear_flag = {}
        self._radio = {}

        self.ready = False # init_func()
        self.bot = bot
        self.queue_limit = config['bot']['queue_limit']
        self.nothing_playing.start()
        self.player.start()

    # ======================================= #

    async def init_new_guild(self, guild):
        _id = guild.id
        self.play_message[_id] = None
        self.now_playing[_id] = False
        self._radio[_id] = False
        self.clear_flag[_id] = False
        self._loop[_id] = 0
        self._pause[_id] = False
        self._queue[_id] = []
        self.no_playing[_id] = {
            "empty_start": 0,
            "empty_end": 0,
            "alone_start": 0,
            "alone_end": 0,
        }

    async def init_func(self):
        for guild in self.bot.guilds:
            _id = guild.id

            self.play_message[_id] = None
            self.now_playing[_id] = False
            self._radio[_id] = False
            self.clear_flag[_id] = False
            self._loop[_id] = 0
            self._pause[_id] = False
            self._queue[_id] = []
            self.no_playing[_id] = {
                "empty_start": 0,
                "empty_end": 0,
                "alone_start": 0,
                "alone_end": 0,
            }

            for member in guild.members:
                if member.id == config['bot']['id']:
                    try:
                        voice_ch = member.voice.channel
                        await voice_ch.connect()
                    except: pass
                    break
        self.ready = True

    # ======================================= #

    async def check_member_voice(self, ctx):
        try: ctx_author = ctx.message.author
        except: ctx_author = ctx.author

        try: user_ch = ctx_author.voice.channel
        except:
            await ctx.send(embed = discord.Embed(title = "**Вы не находитесь ни в одном из каналов!**", color=config['color']['red']))
            return False
        return user_ch
    
    async def check_bot_voice(self, ctx, mode, without_print=False):
        try: ctx_author = ctx.message.author
        except: ctx_author = ctx.author
        user_ch = ctx_author.voice.channel

        voice_ch = get(self.bot.voice_clients, guild=ctx.guild)
        if voice_ch: voice_ch = voice_ch.channel

        if user_ch:
            if str(user_ch.type) == "stage_voice":
                if not without_print:
                    await ctx.send(embed = discord.Embed(title = "**Бот не может использоваться на трибунах**", description = "Если бот уже на трибуне - либо удалите ее, либо попробуйте поиграть с ботом в молчанку. Интересно кто выиграет...", color=config['color']['red']))
                return False

        if mode == "join":
            if voice_ch == None:
                try:
                    await user_ch.connect()
                    bot_member_obj = ctx.guild.get_member(config['bot']['id'])
                    await bot_member_obj.edit(deafen=True)
                    return True
                except: return False
            elif voice_ch.id != user_ch.id:
                if not without_print:
                    await ctx.send(embed = discord.Embed(title = "**Бот используется в другом канале.**", color=config['color']['red']))
                return False
            else:
                if not without_print:
                    await ctx.send(embed = discord.Embed(title = "**Бот уже в вашем канале.**", color=config['color']['red']))
                return False
        
        elif mode == "leave":
            if voice_ch == None:
                if not without_print:
                    await ctx.send(embed = discord.Embed(title = "**Бот не находиться ни в одном из каналов!**", color=config['color']['red']))
                return False
            elif voice_ch.id != user_ch.id:
                if not without_print:
                    await ctx.send(embed = discord.Embed(title = "**Бот используется в другом канале.**", color=config['color']['red']))
                return False
            else:
                await get(self.bot.voice_clients, guild=ctx.guild).disconnect()
                return True

    async def check_member_and_bot_voice(self, ctx):
        try: ctx_author = ctx.message.author
        except: ctx_author = ctx.author
        user_ch = ctx_author.voice.channel

        if user_ch:
            if str(user_ch.type) == "stage_voice":
                await ctx.send(embed = discord.Embed(title = "**Бот не может использоваться на трибунах**", description = "Если бот уже на трибуне - либо удалите ее, либо попробуйте поиграть с ботом в молчанку. Интересно кто выиграет...", color=config['color']['red']))
                return False

        voice_ch = get(self.bot.voice_clients, guild=ctx.guild)
        if not voice_ch:
            await ctx.send(embed = discord.Embed(title = "**Бот не находиться ни в одном из каналов!**", color=config['color']['red']))
            return False
        
        if user_ch.id != voice_ch.channel.id:
            await ctx.send(embed = discord.Embed(title = "**Вы находитесь в другом канале!**", color=config['color']['red']))
            return False
        else: return voice_ch

    # ======================================= #

    async def search(self, request):
        try:
            with YoutubeDL(YDL_OPTS) as ydl:
                if "https://www.youtube.com/" in request or "https://youtu.be" in request:
                    info = ydl.extract_info(request, download=False)
                    return ("https://www.youtube.com/watch?v="+info['id'], info['formats'][0]['url'], info['title'], info['categories'])
                try: r_get(request)
                except: info = ydl.extract_info(f"ytsearch:{request}", download=False)['entries'][0]
            return ("https://www.youtube.com/watch?v="+info['id'], info['formats'][0]['url'], info['title'], info['categories'])
        except Exception as e:
            return [None, e, None, None]
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id == config['bot']['id']:
            if after.channel is None:
                _id = before.channel.guild.id
                self.clear_flag[_id] = True
                self._loop[_id] = 0
                self._pause[_id] = False
                self._radio[_id] = False
                self._queue[_id] = []
                if self.now_playing[_id]:
                    print("[ debug ] NOW")
                    try: await self.play_message[_id].delete()
                    except: pass
                self.now_playing[_id] = False
                await sleep(1.5)
                self.clear_flag[_id] = False
            elif str(after.channel.type) == "stage_voice":
                print("[ STAGE CHANNEL ] guild:", before.channel.guild.id)
    
    # ======================================= #

    @tasks.loop()
    async def nothing_playing(self):
        await sleep(10)
        #print("[ DEBUG ] nothing_playing() start:", time())
        for guild in self.bot.guilds:
            guild_id=guild.id
            voice_ch = get(self.bot.voice_clients, guild=guild)
            if voice_ch != None:
                queue_is_empty = self._queue[guild_id] == []
                bot_alone = len(voice_ch.channel.members) < 2

                if queue_is_empty:
                    if self.no_playing[guild_id]["empty_start"] == 0:
                        self.no_playing[guild_id]["empty_start"] = int(time())
                    self.no_playing[guild_id]["empty_end"] = int(time())
                else:
                    self.no_playing[guild_id]["empty_start"] = 0
                    self.no_playing[guild_id]["empty_end"] = 0

                if bot_alone:
                    if self.no_playing[guild_id]["alone_start"] == 0:
                        self.no_playing[guild_id]["alone_start"] = int(time())
                    self.no_playing[guild_id]["alone_end"] = int(time())
                else:
                    self.no_playing[guild_id]["alone_start"] = 0
                    self.no_playing[guild_id]["alone_end"] = 0
                
                empty = self.no_playing[guild_id]["empty_end"] - self.no_playing[guild_id]["empty_start"]
                alone = self.no_playing[guild_id]["alone_end"] - self.no_playing[guild_id]["alone_start"]
                #print("[ DEBUG ] no_playing() ->", guild_id, empty, alone)

                if (empty > 300) or (alone > 30):
                    self.no_playing[guild_id] = {
                        "empty_start": 0,
                        "empty_end": 0,
                        "alone_start": 0,
                        "alone_end": 0,
                    }
                    try: await self.play_message[guild_id].delete()
                    except: pass
                    try: await voice_ch.disconnect()
                    except Exception as e: print(f"[{guild_id}][i] Disconnected with error: {e}")
                    return
        #print("[ DEBUG ] nothing_playing() end:", time())  

    @tasks.loop(seconds=1)
    async def player(self):
        if not self.ready: await sleep(5)
        for guild in self.bot.guilds:
            _id = guild.id

            voice = get(self.bot.voice_clients, guild=guild)
            if voice != None: # Для тупых которые кикают бота при подключении, а потом он багуется
                flagx=False
                for member in voice.channel.members:
                    if member.id == config['bot']['id']:
                        flagx=True
                        break
                if not flagx:
                    try:
                        await voice.disconnect()
                        await voice.channel.connect()
                    except: pass

            if self._queue[_id] != []:
                voice = get(self.bot.voice_clients, guild=guild)
                if voice == None: continue
                else:
                    try: await voice.channel.connect()
                    except: pass

                if voice.is_playing() or voice.is_paused():
                    self.now_playing[_id] = True
                    continue

                if self.now_playing[_id]:
                    try: await self.play_message[_id].delete()
                    except:
                        print("[x] player() -> play_message.delete() error. guild:", guild)
                        self._queue[_id]=[]
                        continue

                    if self._loop[_id] == 0:
                        try: self._queue[_id].pop(0)
                        except: pass
                    elif self._loop[_id] == 2:
                        track = self._queue[_id][0]
                        self._queue[_id].append(track)
                        self._queue[_id].pop(0)
                    self.now_playing[_id] = False

                else:
                    ctx = self._queue[_id][0]["ctx"]
                    author = self._queue[_id][0]["author"]
                    url = self._queue[_id][0]["url"]
                    sound_url = self._queue[_id][0]["sound_url"]
                    title = self._queue[_id][0]["title"]

                    self.play_message[_id] = await ctx.send(embed = discord.Embed(
                        title = "**Сейчас играет:**",
                        description = f"[{title}]({url}) \n`({author})`",
                        color=config['color']['main']
                    ))

                    try: voice.play(FFmpegPCMAudio(sound_url, **FFMPEG_OPTS))
                    except:
                        print("[x] player() -> voice.play error. guild:", guild)
                        self._queue[_id]=[]
                        try: await self.play_message[_id].delete()
                        except: pass
                        continue
                    if self._pause[_id]: voice.pause()

    # ======================================= #

    @commands.command(aliases=['p'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def play(self, ctx, *request):
        _id = ctx.guild.id

        slash_mode=False
        try: ctx.message.author
        except: slash_mode=True

        user_ch = await self.check_member_voice(ctx)
        if not user_ch: return

        await self.check_bot_voice(ctx, "join", without_print=True)
        voice_ch = await self.check_member_and_bot_voice(ctx)
        if not voice_ch: return

        request=" ".join(request)
        if request == "":
            await ctx.send(embed = discord.Embed(title = "**Укажите название трека или ссылку на него**", color=config['color']['red']))
            return
        if len(self._queue[_id]) > self.queue_limit-1:
            await ctx.send(embed = discord.Embed(title = "**Максимальный размер очереди**", description = f"Лимит позиций в очереди: **{self.queue_limit}**", color=config['color']['red']))
            return
        
        if slash_mode: slash_msg = await ctx.send("Загрузка...")

        if "spotify.com" in request: # Spotify
            error=0
            try:
                playlist=[]
                client_id = config['spotify']['client_id']
                secret = config['spotify']['secret']
                auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=secret)
                spotify = spotipy.Spotify(auth_manager=auth_manager)

                def get_track(url):
                    result = spotify.track(url)
                    name = result['name']
                    artists = result['artists'][0]['name']
                    return name+' - '+artists

                if "spotify.com/playlist" in request:
                    result = spotify.playlist(request)
                    result = result['tracks']
                    for track in result['items']:
                        if self.clear_flag[_id]: return
                        try:
                            tmp = track['track']['uri']
                            tmp = tmp.split(":")
                            tmp = "https://open.spotify.com/track/"+tmp[-1]
                            playlist.append(get_track(tmp))
                        except Exception as e:
                            print('[ DEBUG ] play() -> Ошибка при обработке spotify-трека (пропущен)')
                elif "spotify.com/album" in request:
                    result = spotify.album(request)
                    result = result['tracks']
                    for track in result['items']:
                        if self.clear_flag[_id]: return
                        try:
                            tmp = track['external_urls']['spotify']
                            playlist.append(get_track(tmp))
                        except Exception as e:
                            print('Ошибка при обработке spotify-трека (пропущен)')
                elif "spotify.com/artist" in request:
                    result = spotify.artist_top_tracks(request)
                    result = result['tracks']
                    for track in result:
                        if self.clear_flag[_id]: return
                        try:
                            tmp = track['uri']
                            tmp = tmp.split(":")
                            tmp = "https://open.spotify.com/track/"+tmp[-1]
                            playlist.append(get_track(tmp))
                        except Exception as e:
                            print('Ошибка при обработке spotify-трека (пропущен)')
                elif "spotify.com/track" in request:
                    playlist.append(get_track(request))
                else:
                    error=1
            except:
                error=1
            if error:
                description = "На данный момент бот поддерживает следующие функции из spotify:\n- Проигрывание трека\n- Проигрывание альбома\n- Проигрывание топа исполнителя"
                await ctx.send(embed = discord.Embed(title = "**Spotify-ссылка не распознана!**", description=description, color=0xec2e34))
                return

        elif '&list=' in request or '?list=' in request: # YT-плейлист
            try:
                playlist=[]
                loading_msg = await ctx.send('Загрузка информации о плейлисте...')
                with YoutubeDL({"ignoreerrors": True, "quiet": True}) as ydl:
                    playlist_dict = ydl.extract_info(request, download=False)
                    for i in playlist_dict['entries']:
                        try:
                            if self.clear_flag[_id]: return
                            playlist.append(i['webpage_url'])
                            if len(playlist)+len(self._queue)==self.queue_limit: break
                            await sleep(0.1)
                        except: pass
            except: pass

            try: await loading_msg.delete()
            except: pass
        else:
            playlist=[request]

        if slash_mode: await slash_msg.edit(content=f"Запрос: `{request}`")

        count = len(self._queue[_id])
        for track in playlist:
            print(f'[{_id}][►] {track}')

            yt_url, yt_sound_url, yt_title, categories = await self.search(track)
            if yt_url == None: # yt_sound_url == error_str
                if len(playlist) == 1:
                    description = f"Вероятно вы пытаетесь:\n**- Проиграть стрим**\n**- Проиграть видео с возрастным ограничением**\n**- Проиграть видео недоступное в регионе Европы**\n\nПодробнее об ошибке:\n||{yt_sound_url}||"
                    await ctx.send(embed = discord.Embed(title = f"**Трек недоступен!**", description=description, color=config['color']['red']))
                continue
            
            if self.clear_flag[_id]: return
            voice = get(self.bot.voice_clients, guild=ctx.guild)
            if voice == None: return
            
            yt_title=yt_title.replace("[", "⌠")
            yt_title=yt_title.replace("]", "⌡")
            self._queue[_id].append({"ctx":ctx, "author":ctx.author, "url":yt_url, "sound_url":yt_sound_url, "title":yt_title, "categories":categories})
            count+=1
            if count > self.queue_limit-1: return

            await sleep(0.7)
            if self.clear_flag[_id]: return
            await sleep(0.7)
            if self.clear_flag[_id]: return
            await sleep(0.7)
            if self.clear_flag[_id]: return

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def join(self, ctx):
        user_ch = await self.check_member_voice(ctx)
        if not user_ch: return

        check = await self.check_bot_voice(ctx, "join")
        if not check: return

        try: ctx.message.author
        except: await ctx.send("`Бот зашел в канал`")

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def leave(self, ctx):
        user_ch = await self.check_member_voice(ctx)
        if not user_ch: return

        check = await self.check_bot_voice(ctx, "leave")
        if not check: return

        try: ctx.message.author
        except: await ctx.send("`Бот вышел из канала`")

    @commands.command(aliases=['s'])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def skip(self, ctx):
        user_ch = await self.check_member_voice(ctx)
        if not user_ch: return

        _id = ctx.guild.id
        user_bot_ch = await self.check_member_and_bot_voice(ctx)
        if user_bot_ch:
            self._pause[_id] = False
            if self._loop[_id] == 1: self._loop[_id] = 0
            user_bot_ch.stop()
            try: ctx.message.author
            except:
                if self._queue[_id] == []:
                    await ctx.send("`Очередь пуста`")
                else:
                    await ctx.send("`Трек пропущен`")
        else: return

    @commands.command(aliases=["stop"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def clear(self, ctx):
        user_ch = await self.check_member_voice(ctx)
        if not user_ch: return

        _id = ctx.guild.id
        user_bot_ch = await self.check_member_and_bot_voice(ctx)
        if user_bot_ch:
            self.now_playing[_id] = False
            self.clear_flag[_id] = True
            self._pause[_id] = False
            self._radio[_id] = False
            self._loop[_id] = 0
            self._queue[_id] = []
            user_bot_ch.stop()
            try: ctx.message.author
            except: await ctx.send("`Очередь очищена`")
            await sleep(1.5)
            self.clear_flag[_id]=False
        else: return

    @commands.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def remove(self, ctx, num):
        user_ch = await self.check_member_voice(ctx)
        if not user_ch: return

        _id = ctx.guild.id
        user_bot_ch = await self.check_member_and_bot_voice(ctx)
        if user_bot_ch:
            try: num = int(num)
            except:
                await ctx.send(embed = discord.Embed(title = "**Вы должны указать номер трека (цифра/число)**", color=config['color']['red']))
                return
            if num < 1 or num > len(self._queue[_id]):
                await ctx.send(embed = discord.Embed(title = "**В очереди нет трека под таким номером**", color=config['color']['red']))
                return
            if num == 1:
                user_bot_ch.stop()
                await ctx.send(embed = discord.Embed(title = f"**Трек __№1__ удален из очереди**", color=config['color']['gray']))
            else:
                self._queue[_id].pop(num-1)
                await ctx.send(embed = discord.Embed(title = f"**Трек __№{num}__ удален из очереди**", color=config['color']['gray']))
        else: return

    @commands.command(aliases=['q'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def queue(self, ctx):
        _id = ctx.guild.id
        msg = ""
        for i in range(len(self._queue[_id])):
            title = str(self._queue[_id][i]['title'])
            url = self._queue[_id][i]['url']
            author = self._queue[_id][i]['author']

            if len(title) > 34:
                title = title[:39]+"..."
            msg += str(i+1) + f") [{title}]({url}) - {author}\n"

            if len(self._queue[_id])-i-1 == 0: break
            if i+1 == 10:
                msg += "`... еще "+str(len(self._queue[_id])-i-1)+"`"
                break

        if msg == "":
            self._pause[_id]=False
            self._loop[_id]=0
            msg = "```~ Очередь пуста ~```"
        
        extra = ""
        if self._pause[_id]: extra += "`[● На паузе]` "
        if self._loop[_id] == 1: extra += "`[● Повтор трека]` "
        if self._loop[_id] == 2: extra += "`[● Повтор очереди]` "
        if self._radio[_id] == True: extra += "`[● Радио]`"
        if extra: extra+= "\n"
        
        await ctx.send(embed = discord.Embed(title = "**Очередь воспроизведения:**", description = extra+msg, color=config['color']['main']))

    @commands.command(aliases=['resume'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pause(self, ctx):
        user_ch = await self.check_member_voice(ctx)
        if not user_ch: return

        user_bot_ch = await self.check_member_and_bot_voice(ctx)
        if not user_bot_ch: return
        
        _id = ctx.guild.id
        if self._pause:
            user_bot_ch.resume()
            self._pause[_id] = False
            await ctx.send(embed = discord.Embed(title = "**Трек снят с паузы**", color=config['color']['gray']))
        else:
            user_bot_ch.pause()
            self._pause[_id] = True
            await ctx.send(embed = discord.Embed(title = "**Трек поставлен на паузу**", color=config['color']['gray']))

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def loop(self, ctx):
        user_ch = await self.check_member_voice(ctx)
        if not user_ch: return

        user_bot_ch = await self.check_member_and_bot_voice(ctx)
        if not user_bot_ch: return

        _id = ctx.guild.id
        if not self._loop[_id]:
            self._loop[_id] = 1
            await ctx.send(embed = discord.Embed(title = "**Повтор текущего трека включен**", color=config['color']['gray']))
        else:
            self._loop[_id] = 0
            await ctx.send(embed = discord.Embed(title = "**Повтор выключен**", color=config['color']['gray']))

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def loop_all(self, ctx):
        user_ch = await self.check_member_voice(ctx)
        if not user_ch: return

        user_bot_ch = await self.check_member_and_bot_voice(ctx)
        if not user_bot_ch: return

        _id = ctx.guild.id
        if not self._loop[_id]:
            self._loop[_id] = 2
            await ctx.send(embed = discord.Embed(title = "**Повтор всей очереди включен**", color=config['color']['gray']))
        else:
            self._loop[_id] = 0
            await ctx.send(embed = discord.Embed(title = "**Повтор выключен**", color=config['color']['gray']))

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def radio(self, ctx, *request):
        user_ch = await self.check_member_voice(ctx)
        if not user_ch: return

        await self.check_bot_voice(ctx, "join", without_print=True)
        voice_ch = await self.check_member_and_bot_voice(ctx)
        if not voice_ch: return

        _id = ctx.guild.id
        request=" ".join(request)
        if request == "":
            if self._radio[_id]:
                self._radio[_id] = False
                await ctx.send(embed = discord.Embed(title = "**Радио выключено**", color=config['color']['main']))
            else:
                await ctx.send(embed = discord.Embed(title = "**Укажите жанр/поисковое слово**", description = "Чем короче и обширнее запрос - тем выше точность подбора треков.\nПодробнее - **%radio_info** (%ri)", color=config['color']['red']))
        else:
            if self._radio[_id]:
                self._radio[_id] = False
                await ctx.send(embed = discord.Embed(title = "**Радио перенастроено**", description = "Поиск волны. Подождите 10 секунд", color=config['color']['main']))
                await sleep(10) # TODO Может быть дублирование при долгом поиске песни в цикле радио
            else:
                await ctx.send(embed = discord.Embed(title = "**Радио включено**", description = "- Выключить радио: **%radio**\n- Перенастроить радио: **%radio [новый жанр]**\n- Подробнее про работу радио: **%radio_info** (%ri)", color=config['color']['main']))
            
            self._radio[_id] = True
            self._loop[_id] = 0

            last_songs = []
            attempts=0
            while self._radio[_id]:
                if self._queue[_id] == []:
                    rdm_word = choice(words)
                    rdm_word2 = choice(words)
                    if len(request.split()) < 3: rdm_request = f"music {request} {rdm_word}"
                    else: rdm_request = f"music {request} {rdm_word} {rdm_word2}"

                    if self.clear_flag[_id]: return
                    voice = get(self.bot.voice_clients, guild=ctx.guild)
                    if voice == None: return

                    yt_url, yt_sound_url, yt_title, categories = await self.search(rdm_request)
                    if "Music" not in categories or yt_url in last_songs:
                        attempts+=1
                    else:
                        self._queue[_id].append({"ctx":ctx, "author":ctx.author, "url":yt_url, "sound_url":yt_sound_url, "title":yt_title, "categories":categories})
                        last_songs.append(yt_url)
                        print(f'[{_id}][► RADIO] {rdm_request}')
                
                if len(last_songs) > 15 or attempts > 6:
                    try: last_songs.pop(0)
                    except: pass
                    attempts=0
                await sleep(1)
    
    @commands.command(aliases=['ri'])
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def radio_info(self, ctx):
        msg = (
            "● В режиме радио при пустой очереди воспроизведения в нее добавляется трек, наиболее подходящий под введенный жанр/запрос."
            "\n\n● Запрос должен быть не узконаправлен (чтобы при поиске находились разные треки). Еще лучше, если он будет на английском языке. Пример хороших (обширных) запросов: **__Phonk__**, **__Джаз__**, **__Бетховен__**, **__Rap__**."
            "\n\n● Если найденный трек уже проигрывался недавно, то он будет пропущен."
            "\n\n● Если не удается найти новый трек, то будут повторяться недавние."
        )
        await ctx.send(embed = discord.Embed(title = "**__Как работает радио:__**", description = msg, color=config['color']['main']))

    # ======================================= #

    @cog_ext.cog_slash(name = 'play', description = 'Поставить трек в очередь', options = [{'name':'request', 'description':'Запрос/ссылка', 'type':3, 'required':True}], guild_ids=None)
    async def play_slash(self, ctx: SlashContext, request):
        await self.play(ctx, request)
    
    @cog_ext.cog_slash(name = 'radio', description = 'Вкл/выкл радио', options = [{'name':'request', 'description':'Жанр/запрос', 'type':3, 'required':False}], guild_ids=None)
    async def radio_slash(self, ctx: SlashContext, request):
        await self.radio(ctx, request)
    
    @cog_ext.cog_slash(name = 'skip', description = 'Пропустить трек', options = [], guild_ids=None)
    async def skip_slash(self, ctx: SlashContext):
        await self.skip(ctx)
    
    @cog_ext.cog_slash(name = 'queue', description = 'Показать очередь воспроизведения', options = [], guild_ids=None)
    async def queue_slash(self, ctx: SlashContext):
        await self.queue(ctx)
    
    @cog_ext.cog_slash(name = 'pause', description = 'Вкл/выкл паузы', options = [], guild_ids=None)
    async def pause_slash(self, ctx: SlashContext):
        await self.pause(ctx)
    
    @cog_ext.cog_slash(name = 'clear', description = 'Очищение всей очереди воспроизведения', options = [], guild_ids=None)
    async def clear_slash(self, ctx: SlashContext):
        await self.clear(ctx)
    
    @cog_ext.cog_slash(name = 'remove', description = 'Удаляет из очереди трек с указанным номером', options = [{'name':'track_num', 'description':'Номер удаляемого терка в очереди', 'type':4, 'required':True}], guild_ids=None)
    async def remove_slash(self, ctx: SlashContext, track_num):
        await self.remove(ctx, track_num)
    
    @cog_ext.cog_slash(name = 'loop', description = 'Вкл/выкл повтора', options = [], guild_ids=None)
    async def loop_slash(self, ctx: SlashContext):
        await self.loop(ctx)
    
    @cog_ext.cog_slash(name = 'loop_all', description = 'Вкл/выкл повтора всей очереди', options = [], guild_ids=None)
    async def loop_all_slash(self, ctx: SlashContext):
        await self.loop_all(ctx)
    
    @cog_ext.cog_slash(name = 'join', description = 'Призвать бота', options = [], guild_ids=None)
    async def join_slash(self, ctx: SlashContext):
        await self.join(ctx)
    
    @cog_ext.cog_slash(name = 'leave', description = 'Выгнать бота', options = [], guild_ids=None)
    async def leave_slash(self, ctx: SlashContext):
        await self.leave(ctx)

    @cog_ext.cog_slash(name = 'radio_info', description = 'Информация про работу радио', options = [], guild_ids=None)
    async def radio_info_slash(self, ctx: SlashContext):
        await self.radio_info(ctx)


def setup(bot):
    bot.add_cog(Music(bot))