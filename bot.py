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
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    mentionsList = ctx.message.mentions
    victims = []
    perp = ctx.message.author
    
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    #get current value
    c.execute("""SELECT tabloids from ?_player_list WHERE discord_username = ?""", (guild.id, perp.display_name))
    record = c.fetchall
    #update table
    c.execute("""UPDATE ?_player_list (
             SET tabloids = ?
             WHERE discord_username = ?
             )""", (guild.id, int(record[0][0])+1, perp.display_name))   
     
    for mention in mentionsList:
        c.execute("""SELECT tabloids from ?_player_list WHERE discord_username = ?""", (guild.id, mention.display_name))
        record = c.fetchall
        c.execute("""UPDATE ?_player_list (
             SET times_tabloided = ?
             WHERE discord_username = ?
             )""", (guild.id, int(record[0][0])+1, mention.display_name))
        conn.commit()
    conn.close
    
    await ctx.send(f"{perp.display_name} has tabloided {" ".join(victims)}")

#@bot.command(name='leaderboard', help='Shows global statistics of the tabloid')
#queries database and produces a leaderboard
#consider having different sortings, such as tabloids, tabloided, and k/d

#@bot.command(name='stats', help='Shows your personal statistics')
#provide stats for the user who called the command

#@bot.command(name='name', help='Associate your name with your username')
#add text to the username list table

@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS {guild.id}_player_list (
             discord_username string NOT NULL,
             name string NOT NULL,
             tabloids,
             times_tabloided,
             )""")
    #c.execute('insert into player_list(discord_username, name, tabloids, times_tabloided, ratio) values(?, ?, ?, ?, ?)', ('bonk username', 'bonk name', 1, 0))
    c.execute("""CREATE TABLE IF NOT EXISTS {guild.id}_username_list (
             discord_username string NOT NULL,
             name string NOT NULL
             )""")
    conn.commit()

    print(
        f'{bot.user.name} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )
    print(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)