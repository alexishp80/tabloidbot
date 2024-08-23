# bot.py
import os
import sqlite3
import pandas as pd
import numpy as np
import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

help_command = commands.DefaultHelpCommand(
    no_category = 'Commands'
)
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command = help_command)

@bot.command(name='tabloid', help='Tabloids another CNET')
async def add(ctx):
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    mentionsList = ctx.message.mentions
    victims = []
    perp = ctx.message.author
    
    if not mentionsList: 
        #list is empty
        await ctx.send(f"<@{perp.id}> Please mention your victim(s)!")
        return

    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO player_list (discord_username, tabloids, times_tabloided) VALUES (?, 0,0)""", (perp.name,))
    #get current value
    c.execute("""SELECT tabloids from player_list WHERE discord_username = ?""", (perp.name,))
    record = c.fetchone()[0]
    #update table
    c.execute("""UPDATE player_list
             SET tabloids = ?
             WHERE discord_username = ?
             ;""", (int(record)+1, perp.name))   
     
    for mention in mentionsList:
        victims.append(mention.display_name)
        c.execute("""INSERT OR IGNORE INTO player_list (discord_username, tabloids, times_tabloided) VALUES (?, 0,0)""", (mention.name,))
        c.execute("""SELECT times_tabloided from player_list WHERE discord_username = ?""", (mention.name,))
        record = c.fetchone()[0]
        c.execute("""UPDATE player_list 
             SET times_tabloided = ?
             WHERE discord_username = ?
             ;""", (int(record)+1, mention.name))
        conn.commit()
    conn.close
    await ctx.send(f"{perp.display_name} has tabloided {', '.join(victims)}")

def embedrow(row, em):
        if row['name'] is None:
            em.add_field(name=f'**{row['discord_username']}**', value=f'> Tabloids: {row['tabloids']}\n> Times Tabloided: {row['times_tabloided']}\n> K/D Ratio: {row['kd']}',inline=False)
        else:
            em.add_field(name=f'**{row['name']}**', value=f'> Tabloids: {row['tabloids']}\n> Times Tabloided: {row['times_tabloided']}\n> K/D Ratio: {row['kd']}',inline=False)
def fun(row):
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("""SELECT name from username_list WHERE discord_username = ?""", (row['discord_username'],))
    record = c.fetchone()
    if record is None:
        return
    else:
        record = record[0]
        conn.close
        return record
#queries database and produces a leaderboard
#with different sortings, such as tabloids, tabloided, and k/d
@bot.command(name='leaderboard', help='Shows top 5 players and stats')
async def leaderboard(ctx, *arg):
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    query = 'SELECT * from player_list'
    df = pd.read_sql(query, conn)
    df['kd'] = df['tabloids']/df['times_tabloided']
    df.replace([np.inf, -np.inf], np.inf, inplace=True)
    if not arg or arg[0] == "tabloids":
        df = df.sort_values('tabloids', ascending=[False])
        df = df.head(5)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.fillna('-')
        df['name'] = df.apply(fun, axis=1)
        embed = discord.Embed(title="Tabloids Leaderboard", color=0x00ff00)
        df.apply(embedrow, axis=1, em=embed)
        conn.close
        await ctx.send(embed=embed)
    elif(arg[0] == "kd"):
        df = df.sort_values('kd', ascending=[False])
        df = df.head(5)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.fillna('-')
        df['name'] = df.apply(fun, axis=1)
        embed = discord.Embed(title="K/D Ratio Leaderboard", color=0x00ff00)
        df.apply(embedrow, axis=1, em=embed)
        conn.close
        await ctx.send(embed=embed)
    elif(arg[0] == "tabloided"):
        df = df.sort_values('times_tabloided', ascending=[False])
        df = df.head(5)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.fillna('-')
        df['name'] = df.apply(fun, axis=1)
        embed = discord.Embed(title="Most Tabloided Leaderboard", color=0x00ff00)
        df.apply(embedrow, axis=1, em=embed)
        conn.close
        await ctx.send(embed=embed)
    else:
        return

#whole leaderboard
@bot.command(name='global', help='Shows global statistics')
async def global_leaderboard(ctx):
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    query = 'SELECT * from player_list'
    df = pd.read_sql(query, conn)
    df['kd'] = df['tabloids']/df['times_tabloided']
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df = df.sort_values('tabloids')
    df2 = pd.DataFrame({'name': []})
    df2['name'] = df.apply(fun, axis=1)
    df = pd.concat([df2, df], axis=1)
    df = df.fillna('-')
    conn.close
    await ctx.send(f"```{df.head()}```")

#provide stats for the user who called the command
@bot.command(name='stats', help='Shows your personal statistics')
async def stats(ctx):
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    query = "SELECT * from player_list WHERE discord_username = '{}'".format(ctx.message.author.name)
    df = pd.read_sql(query, conn)

    df['kd'] = df['tabloids']/df['times_tabloided']
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df = df.fillna('-')
    conn.close

    embed = discord.Embed(title=f"{ctx.message.author.name}'s stats", color=0x00ff00)
    df = df.head(1)
    embed.add_field(name=f'**Tabloids: {df['tabloids'][0]}**', value=f'** Times Tabloided: {df['times_tabloided'][0]}\n K/D Ratio: {df['kd'][0]}**',inline=False)
    await ctx.send(embed=embed)

@bot.command(name='name', help='Associate your name with your username')
#add text to the username list table
async def name(ctx, arg):
    perp = ctx.message.author
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO username_list (discord_username, name) VALUES (?, ?)""", (perp.name, arg))
    conn.commit()
    conn.close
    await ctx.send("Name updated")
@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS {}(
             discord_username string NOT NULL UNIQUE,
             tabloids,
             times_tabloided
             )""".format("player_list"))
    c.execute("""CREATE TABLE IF NOT EXISTS {} (
             discord_username string NOT NULL UNIQUE,
             name string NOT NULL
             )""".format("username_list"))
    conn.commit()
    conn.close
    print(
        f'{bot.user.name} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )
    print(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)