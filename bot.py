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

@bot.command(name='tabloid', help='Tabloids another CNET')
async def add(ctx):
    mentionsList = ctx.message.mentions
    victims = []
    perp = ctx.message.author
    for mention in mentionsList:
        victims.append(mention.display_name)
    await ctx.send(f"{perp.display_name} has tabloided {" ".join(victims)}")

#@bot.command(name='leaderboard', help='Shows global statistics of the tabloid')
#queries database and produces a leaderboard
#consider having different sortings, such as tabloids, tabloided, and k/d

#@bot.command(name='stats', help='Shows your personal statistics')
#provide stats for the user who called the command


### Restricted to leadership roles ###
#@bot.command(name='amend', help='Fixes a previous tabloid')
#will take in a id which matches the line in the database, used to fix entries if needed

#@bot.command(name='delete', help='Deletes a previous tabloid')
#will delete an entry given the id

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