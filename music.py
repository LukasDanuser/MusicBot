import discord
from discord.ext import commands
from youtube_dl import YoutubeDL


class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        #all the music related stuff
        self.is_playing = False
        self.music_queue = []
        self.queue_loop = []
        self.qLoopBool = False
        self.voiceChannel = ""
        self.currentSong = []
        self.isLoop = False
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {
            'before_options':
            '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -loglevel quiet'
        }

        self.vc = ""

    #searching the item on youtube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item,
                                        download=False)['entries'][0]
            except Exception:
                return False
        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            #get the first url
            m_url = self.music_queue[0][0]['source']
            if self.isLoop == False:
                #remove the first element as you are currently playing it
                self.music_queue.pop(0)
            if len(self.music_queue) <= 0 and self.qLoopBool == True:
                self.music_queue.clear()
                for i in range(0, len(self.queue_loop)):
                    self.music_queue.append(
                        [self.queue_loop[i][0], self.queue_loop[i][1]])
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                         after=lambda e: self.play_next())
        elif self.qLoopBool == True:
            self.music_queue.clear()
            for i in range(0, len(self.queue_loop)):
                self.music_queue.append(
                    [self.queue_loop[i][0], self.queue_loop[i][1]])
            self.play_next
        else:
            self.is_playing = False

    # infinite loop checking
    async def play_music(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            #try to connect to voice channel if you are not already connected

            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])

            if self.isLoop == False:
                self.currentSong = self.music_queue[0][0]
                #remove the first element as you are currently playing it
                self.music_queue.pop(0)
                if len(self.music_queue) <= 0 and self.qLoopBool == True:
                    self.music_queue.clear()
                    for i in range(0, len(self.queue_loop)):
                        self.music_queue.append(
                            [self.queue_loop[i][0], self.queue_loop[i][1]])

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                         after=lambda e: self.play_next())
        elif self.qLoopBool == True:
            self.music_queue.clear()
            for i in range(0, len(self.queue_loop)):
                self.music_queue.append(
                    [self.queue_loop[i][0], self.queue_loop[i][1]])
            await self.play_music()
        else:
            self.is_playing = False

    @commands.command(name="play",
                      aliases=['p'],
                      help="Plays a selected song from youtube")
    async def p(self, ctx, *args):
        query = " ".join(args)
        try:
            voice_channel = ctx.author.voice.channel

            if ctx.voice_client is not None and ctx.voice_client.channel is not voice_channel:

                self.music_queue.clear()
                await ctx.guild.voice_client.disconnect()

            if voice_channel is None:
                #you need to be connected so that the bot knows where to go
                await ctx.send("Connect to a voice channel!")
            else:
                song = self.search_yt(query)
                if type(song) == type(True):
                    await ctx.send(
                        "Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format."
                    )
                else:
                    await ctx.send("Song added to the queue")
                    self.music_queue.append([song, voice_channel])
                    if self.qLoopBool == True:
                        self.queue_loop.append([song, voice_channel])
                    if self.is_playing == False:
                        await self.play_music()
        except:
            await ctx.send(
                "Something went wrong! You're probably not connected to a voice channel!"
            )

    @commands.command(name="join")
    async def join(self, ctx):
        try:
            voice_channel = ctx.author.voice.channel
            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await voice_channel.connect()
            else:
                await self.vc.move_to(voice_channel)
        except:
            await ctx.send("Connect to a voice channel!")

    @commands.command(name="queue",
                      aliases=['q'],
                      help="Displays the current songs in queue")
    async def q(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += self.music_queue[i][0]['title'] + "\n"

        print(retval)
        if retval != "":
            await ctx.send("```" + retval + "```")

            if self.qLoopBool == True:
                await ctx.send("Queue Loop enabled!")
        else:
            await ctx.send("No music in queue")
            if self.qLoopBool == True:
                await ctx.send("Queue Loop enabled!")

    @commands.command(name="leave",
                      aliases=['fuckoff'],
                      help="Laves the voice channel")
    async def leave(self, ctx):
        try:
            ctx.author.voice.channel
            if ctx.voice_client != "":
                if (ctx.voice_client):
                    self.isLoop = False
                    self.qLoopBool = False
                    self.firstSong = ""
                    self.music_queue.clear()
                    self.queue_loop.clear()
                    await ctx.guild.voice_client.disconnect()
                    await ctx.send('Bot left')
            else:
                await ctx.send("Bot is not connected to your voice channel!")
        except:
            await ctx.send("Connect to a voice channel!")

    @commands.command(name="skip", help="Skips the current song being played")
    async def skip(self, ctx):
        try:
            ctx.author.voice.channel
            if ctx.voice_client != "":
                self.vc.stop()
                #try to play next in the queue if it exists
                await self.play_music()
                await ctx.send("Skipped")
            else:
                await ctx.send("Bot is not connected to your voice channel!")
        except:
            await ctx.send("Connect to a voice channel!")

    @commands.command(name="loop")
    async def loop(self, ctx):
        try:
            ctx.author.voice.channel
            if ctx.voice_client != "" and self.vc:
                if self.isLoop == False:
                    self.isLoop = True
                    self.qLoopBool = False
                    self.voiceChannel = ctx.author.voice.channel
                    self.music_queue.insert(
                        0, [self.currentSong, self.voiceChannel])
                    await ctx.send("Looping...")
                else:
                    self.isLoop = False
                    self.music_queue.pop(0)
                    await ctx.send("Stop looping")
            else:
                await ctx.send("Bot is not connected to your voice channel!")
        except:
            await ctx.send("Connect to a voice channel!")

    @commands.command(name="ql", aliases=['queueloop'])
    async def ql(self, ctx):
        try:
            voice_channel = ctx.author.voice.channel
            if ctx.voice_client != "" and self.vc:
                if (self.qLoopBool == False):
                    self.isLoop = False
                    self.queue_loop.clear()
                    self.queue_loop.append([self.currentSong, voice_channel])
                    for i in range(0, len(self.music_queue)):
                        self.queue_loop.append(
                            [self.music_queue[i][0], self.music_queue[i][1]])
                    self.qLoopBool = True
                    await ctx.send("Looping the queue...")
                else:
                    self.queue_loop.clear()
                    self.qLoopBool = False
                    await ctx.send("Stop looping the queue")
            else:
                await ctx.send("Bot is not connected to your voice channel!")
        except:
            await ctx.send("Connect to a voice channel!")

    @commands.command(name="stop")
    async def stop(self, ctx):
        try:
            ctx.author.voice.channel
            if ctx.voice_client != "":
                self.isLoop = False
                self.qLoopBool = False
                self.firstSong = ""
                self.music_queue.clear()
                self.queue_loop.clear()
                await ctx.send("Stopped")
            else:
                await ctx.send("Bot is not connected to your voice channel!")
        except:
            await ctx.send("Connect to a voice channel!")

    @commands.command(name='pause')
    async def pause(self, ctx):
        try:
            if ctx.voice_client != "":
                ctx.author.voice.channel
                self.vc.pause()
                await ctx.send("Paused!")
            else:
                await ctx.send("Bot is not connected to your voice channel!")
        except:
            await ctx.send("Connect to a voice channel!")

    @commands.command(name='resume')
    async def resume(self, ctx):
        try:
            if ctx.voice_client != "":
                ctx.author.voice.channel
                self.vc.resume()
                await ctx.send("Resumed!")
            else:
                await ctx.send("Bot is not connected to your voice channel!")
        except:
            await ctx.send("Connect to a voice channel!")

    @commands.command(name="feedback")
    async def feedback(self, ctx):
        user = await self.bot.fetch_user("773654004332101673")
        if ctx.message.content != "*feedback":
            await user.send(str(ctx.author.name + ": " + ctx.message.content))
            await ctx.send("Thank you for your feedback!")
        else:
            await ctx.send("Please enter a message!")

    @commands.command(name="help")
    async def help(self, ctx):
        await ctx.send('```Commands (prefix: *)' + '\n\n' +
                       'play  | Play music  | Aliases: p' + '\n' +
                       'join  | Bot joins your channel' + '\n' +
                       'skip  | Skip the current song' + '\n' +
                       'queue | Show whats in the queue | Aliases: q' + '\n' +
                       'leave | Leaves the voice channel  | Aliases: fuckoff' +
                       '\n'
                       'help  | Shows this help page' + '\n' +
                       'loop  | Loop current song' + '\n' +
                       'queueloop  | Loop the whole queue  | Aliases: ql' +
                       '\n' + 'stop | Stops playing and clears the queue' +
                       '\n' +
                       'feedback | You can send feedback or report a bug' +
                       '\n' + 'pause | Pause the current song' + '\n' +
                       'resume  | Resumes the paused song```')
