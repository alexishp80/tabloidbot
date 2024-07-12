# bot.py
import os
import sqlite3
import pandas as pd
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


    #do sql stuff here
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
    
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS player_list (
             discord_username string NOT NULL,
             name string NOT NULL,
             tabloids,
             times_tabloided,
             ratio
             )""")
    c.execute('insert into player_list(discord_username, name, tabloids, times_tabloided, ratio) values(?, ?, ?, ?, ?)', ('bonk username', 'bonk name', 1, 0, 1))
    #want to dm everyone with current members role to set this table up
    c.execute("""CREATE TABLE IF NOT EXISTS tabloid_list (
             id,
             perp string NOT NULL,
             victims
             )""")
    c.execute('insert into tabloid_list(id, perp, victims) values(?, ?, ?)', (0, 'tenderbread', 'tenderbread,alexis'))
    #storing victims will probably require stringifying a list, which can then be converted back into a list if edits are needed
    conn.commit()

    print(
        f'{bot.user.name} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )
    print(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)