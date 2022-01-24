import discord
import os
from keep_alive import keep_alive
from music import music
from discord.ext import commands

client = commands.Bot(command_prefix='*', case_insensitive=True)
client.remove_command('help')
client.add_cog(music(client))


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Game(name="*help"))


keep_alive()
client.run(os.environ['TOKEN'])
