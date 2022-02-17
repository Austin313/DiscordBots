import discord
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import youtube_dl
import sys

from random import choice

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' 
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


client = commands.Bot(command_prefix='-')

status = ['Jamming out to music!', 'Eating!', 'Sleeping!']
queues = {}

@client.event
async def on_ready():
    change_status.start()
    print('Bot is online!')

@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='general')
    await channel.send(f'Welcome {member.mention}!  Ready to jam out? See `?help` command for details!')
        
@client.command(name='ping', help='This command returns the latency')
async def ping(ctx):
    await ctx.send(f'**Pong!** Latency: {round(client.latency * 1000)}ms')

@client.command(name='hello', help='This command returns a random welcome message')
async def hello(ctx):
    responses = ['yo']
    await ctx.send(choice(responses))

@client.command(name='die', help='This command returns a random last words')
async def die(ctx):
    responses = ['why would you do this!!!']
    await ctx.send(choice(responses))

@client.command(name='credits', help='This command returns the credits')
async def credits(ctx):
    await ctx.send('Made with love, by Juicebox')
    
@client.command(name='join', help='This command makes the bot join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    
    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()


@client.command(name='remove', help='This command removes an item from the list')
async def remove(ctx, number):
    global queues

    try:
        del(queues[int(number)])
        await ctx.send(f'Your queue is now `{queue}!`')
    
    except:
        await ctx.send('Your queue is either **empty** or the index is **out of range**')
        
def queue(ctx, id):
    if len(queues) > 0 and queues[id] != []:
        voice = ctx.guild.voice_client
        audio = queues[id].pop(0)
        voice.play(audio, after=lambda x=None: queue(ctx, ctx.message.guild.id))


@client.command(name='play',help ='Play a song',aliases=['plays', 'p'])
async def play(ctx, url):
    global queues

    server = ctx.message.guild
    guild_id = ctx.message.guild.id
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    audio = await YTDLSource.from_url(url, loop=client.loop)
    if not voice.is_playing():
        async with ctx.typing():
            voice.play(audio, after=lambda x=None: queue(ctx, guild_id))
            voice.is_playing()
            await ctx.send(f'**Now playing:** {audio.title}')
    else:
        if guild_id in queues:
            queues[guild_id].append(audio)
        else:
            queues[guild_id] = [audio]

        await ctx.send("Added to queue.")

@client.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.pause()

@client.command(name='resume', help='This command resumes the song!')
async def resume(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.resume()

@client.command(name='view', help='This command shows the queue')
async def view(ctx):
    await ctx.send(f'Your queue is now `{queues}!`')

@client.command(name='leave', help='This command stops makes the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()

@client.command(name='skip', help='This command stops the song!')
async def skip(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.stop()

@tasks.loop(seconds=20)
async def change_status():
    await client.change_presence(activity=discord.Game(choice(status)))

client.run('OTM2MDA5ODMyMTExMTUzMTUy.YfG9Fg.AvGI3zJoukMGJPHv94MFeRu-RR0')