# bot.py
import os
import sqlite3
import pandas as pd
import numpy as np
import discord
import my_paginator
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DATABASE = os.getenv('DATABASE')
ID = os.getenv('ID')
BENCHMARKS = [1, 10, 25, 50, 100]

help_command = commands.DefaultHelpCommand(
    no_category = 'Commands',
)
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command = help_command)


async def check_guild(ctx):
    if(ctx.guild is not None): 
        return str(ctx.guild.id) == ID
    else:
        return False


@bot.command(name='tabloid', help='Tabloids another CNET. You must mention your victims.', aliases=["tb"])
@commands.check(check_guild)
async def add(ctx):
    if ctx.message.attachments:
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

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("""INSERT OR IGNORE INTO player_list (discord_username, tabloids, times_tabloided) VALUES (?, 0,0)""", (perp.name,))
        #get current value
        c.execute("""SELECT tabloids from player_list WHERE discord_username = ?""", (perp.name,))
        record = c.fetchone()[0]
        #update table
        c.execute("""UPDATE player_list
                SET tabloids = ?
                WHERE discord_username = ?
                ;""", (int(record)+len(mentionsList), perp.name))   
        
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
        await ctx.message.add_reaction("📸")
        await benchmarks(perp, ctx)
    else:
        await ctx.send(f"Please include your tabloid photo with your message.")

async def benchmarks(user, ctx):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""SELECT tabloids from player_list WHERE discord_username = ?""", (user.name,))
    record = int(c.fetchone()[0])
    conn.close()
    # benchmarks are defined in top of file
    if record in BENCHMARKS:
        user = await bot.fetch_user(ctx.message.author.id)
        if record == 1:
            await user.send("Congrats on your first tabloid!")
        else: 
            print("bruh")
            await user.send("You have reached " + record + " tabloids!")

@bot.command(name='undo', help='Undo a tabloid.')
@commands.check(check_guild)
async def sub(ctx):
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    if "section leader" in [role.name for role in ctx.author.roles] or "squid leaders" in [role.name for role in ctx.author.roles] or ctx.message.author == ctx.message.mentions[0]:
        
        victims = []
        mentionsList = ctx.message.mentions[1:]
        perp = ctx.message.mentions[0]
        
        if not mentionsList:
            await ctx.send(f"Make sure to mention yourself and your innocent victim.")
        else:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            #get current value
            c.execute("""SELECT tabloids from player_list WHERE discord_username = ?""", (perp.name,))
            record = c.fetchone()[0]
            #update table
            c.execute("""UPDATE player_list
                    SET tabloids = ?
                    WHERE discord_username = ?
                    ;""", (int(record)-len(mentionsList), perp.name))   
            
            for mention in mentionsList:
                victims.append(mention.display_name)
                c.execute("""INSERT OR IGNORE INTO player_list (discord_username, tabloids, times_tabloided) VALUES (?, 0,0)""", (mention.name,))
                c.execute("""SELECT times_tabloided from player_list WHERE discord_username = ?""", (mention.name,))
                record = c.fetchone()[0]
                c.execute("""UPDATE player_list 
                    SET times_tabloided = ?
                    WHERE discord_username = ?
                    ;""", (int(record)-1, mention.name))
                conn.commit()
            conn.close
            await ctx.message.add_reaction("✅")
            #await ctx.send(f"Undid tabloid by {perp.display_name} for victims {', '.join(victims)}")
    else:
        await ctx.send(f"Please contact leadership to run this command.")


def embedrow(row, em):
        if row['name'] == "-" or row['name'] is None:
            em.add_field(name=f"**{row['discord_username']}**", value=f">>> Tabloids: {row['tabloids']}\nTimes Tabloided: {row['times_tabloided']}\nK/D Ratio: {row['kd']}",inline=False)
        else:
            em.add_field(name=f"**{row['name']}**", value=f">>> Tabloids: {row['tabloids']}\nTimes Tabloided: {row['times_tabloided']}\nK/D Ratio: {row['kd']}",inline=False)
def fun(row):
    conn = sqlite3.connect(DATABASE)
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
async def leaderboard(ctx, arg:  str = commands.parameter(default="tabloids", description="tabloids, tabloided, or kd for various tables")):
    user = await bot.fetch_user(ctx.message.author.id)
    conn = sqlite3.connect(DATABASE)
    query = 'SELECT * from player_list'
    df = pd.read_sql(query, conn)
    if(ctx.guild is not None):
        await ctx.message.delete()
        await user.send("Please use the `global` command in a direct message with the bot to avoid spamming the server.")
    if(len(df) == 0):
        await user.send("Sorry, there's nothing to display yet.")
        return    
    df['kd'] = round(df['tabloids']/df['times_tabloided'], 2)
    df.replace([np.inf, -np.inf], np.inf, inplace=True)
    if arg is None or arg == "kd":
        df = df.sort_values('kd', ascending=[False])
        df = df.head(5)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.fillna('-')
        df['name'] = df.apply(fun, axis=1)
        embed = discord.Embed(title="K/D Ratio Leaderboard", color=0x00ff00)
        df.apply(embedrow, axis=1, em=embed)
        conn.close
        await user.send(embed=embed)
    elif(arg == "tabloids"):
        df = df.sort_values('tabloids', ascending=[False])
        df = df.head(5)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.fillna('-')
        df['name'] = df.apply(fun, axis=1)
        embed = discord.Embed(title="Tabloids Leaderboard", color=0x00ff00)
        df.apply(embedrow, axis=1, em=embed)
        conn.close
        await user.send(embed=embed)
    else: #(arg == "tabloided")
        df = df.sort_values('times_tabloided', ascending=[False])
        df = df.head(5)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.fillna('-')
        df['name'] = df.apply(fun, axis=1)
        embed = discord.Embed(title="Most Tabloided Leaderboard", color=0x00ff00)
        df.apply(embedrow, axis=1, em=embed)
        conn.close
        await user.send(embed=embed)

    if(ctx.guild is not None):
        await ctx.message.delete()
        await user.send("Please use the `leaderboard` command in a direct message with the bot to avoid spamming the server.")

#whole leaderboard
@bot.command(name='global', help='Shows global statistics')
async def global_leaderboard(ctx):
    user = await bot.fetch_user(ctx.message.author.id)
    conn = sqlite3.connect(DATABASE)
    query = 'SELECT * from player_list'
    df = pd.read_sql(query, conn)
    if(ctx.guild is not None):
        await ctx.message.delete()
        await user.send("Please use the `global` command in a direct message with the bot to avoid spamming the server.")
    if(len(df) == 0):
        await user.send("Sorry, there's nothing to display yet.")
        return
    df['kd'] = round(df['tabloids']/df['times_tabloided'], 2)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df = df.sort_values('tabloids', ascending=[False])
    df2 = pd.DataFrame({'name': []})
    df2['name'] = df.apply(fun, axis=1)
    df = pd.concat([df2, df], axis=1)
    df = df.fillna('-')
    conn.close

    ## build embed
    embeds = []
    chunk_size = 5
    for i in range(0, len(df), chunk_size):
        embed = discord.Embed(title="Global Leaderboard", color=0x00ff00)
        df_1 = df.iloc[i:i+chunk_size,:]
        df_1.apply(embedrow, axis=1, em=embed)
        embeds.append(embed)

    # send embed
    await my_paginator.Simple().start(ctx, pages=embeds, sendAsDM=True, user=user)
    

#provide stats for the user who called the command
@bot.command(name='stats', help='Shows your personal statistics')
async def stats(ctx):
    user = await bot.fetch_user(ctx.message.author.id)
    if(ctx.guild is not None):
        await ctx.message.delete()
        await user.send("Please use the `stats` command in a direct message with the bot to avoid spamming the server.")
    conn = sqlite3.connect(DATABASE)
    query = "SELECT * from player_list WHERE discord_username = '{}'".format(ctx.message.author.name)
    df = pd.read_sql(query, conn)
    if(len(df) == 0):
        await user.send("Sorry, you don't have any stats to display yet!")
        return
    df['kd'] = round(df['tabloids']/df['times_tabloided'], 2)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df = df.fillna('-')
    conn.close

    embed = discord.Embed(title=f"{ctx.message.author.name}'s stats", color=0x00ff00)
    df = df.head(1)
    embed.add_field(name=f"**Tabloids: {df['tabloids'][0]}**", value=f"**Times Tabloided: {df['times_tabloided'][0]}\nK/D Ratio: {df['kd'][0]}**",inline=False)
    await user.send(embed=embed)

@bot.command(name='name', help='Associate your name with your username')
#add text to the username list table
@commands.check(check_guild)
async def name(ctx, arg: str = commands.parameter(description="Your name")):
    perp = ctx.message.author
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO username_list (discord_username, name) VALUES (?, ?)""", (perp.name, arg))
    conn.commit()
    conn.close
    await ctx.send("Name updated")

@bot.command(name='docs', help='Provides link for more in-depth documentation')
async def docs(ctx):
    await ctx.send("[Here you go!](<https://github.com/alexishp80/tabloidbot/blob/main/docs/usage.md>)")

@bot.command(name='export', help='Exports database as Excel spreadsheet')
async def export(ctx):
    user = await bot.fetch_user(ctx.message.author.id)
    if(ctx.guild is not None):
            await ctx.message.delete()
            await user.send("Please use the `export` command in a direct message with the bot to avoid spamming the server.")
    conn = sqlite3.connect(DATABASE)
    query = 'SELECT * from player_list'
    conn.close
    df = pd.read_sql(query, conn)
    if(len(df) == 0):
        await user.send("Sorry, there's nothing to display yet.")
        return
    excel_file_path = 'exported_tabloid.xlsx'
    df.to_excel(excel_file_path, index=False)
    await ctx.send(file=discord.File(excel_file_path))
    os.remove(excel_file_path)



@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    
    conn = sqlite3.connect(DATABASE)
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
    # role = discord.utils.find(lambda r: r.name == 'current members', guild.roles)
    # for member in guild.members:
    #    if role in member.roles:
    #        await member.send("Hi " + member.name + " welcome to the CNET Tabloid!\nThe rules can be found at https://tinyurl.com/mpmkbx9t\nUsage instructions can be found here: https://tinyurl.com/47ppxbvj")
bot.run(TOKEN)