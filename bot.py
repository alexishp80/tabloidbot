# bot.py
import os
import random
import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.command(name='tabloid')
async def add(ctx):
    mentionsList = ctx.message.mentions
    victims = []
    perp = ctx.message.author
    for mention in mentionsList:
        victims.append(mention.name)
        await ctx.send(mention.name)
    print(victims)
    print(perp)
    #response = discord.Message.mentions
    #await ctx.send(ctx.author)



@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{bot.user.name} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )
    print(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)