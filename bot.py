# bot.py
import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import discord
import my_paginator
from dotenv import load_dotenv
from discord.ext import commands
import logging
import fcntl

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DATABASE = os.getenv('DATABASE')
ID = os.getenv('ID')
BENCHMARKS = [1, 10, 25, 50, 100]


# --- single-instance lock ---
LOCK_PATH = "/tmp/tabloidbot.lock"
_lock_handle = None  

def acquire_single_instance_lock(path=LOCK_PATH):
    global _lock_handle
    lock_file = open(path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"Another instance is already running (lock held on {path}). Exiting.")
        sys.exit(1)
    lock_file.write(str(os.getpid()))
    lock_file.flush()
    _lock_handle = lock_file

acquire_single_instance_lock()
# -------------------------


help_command = commands.DefaultHelpCommand(
    no_category = 'Commands',
)
intents = discord.Intents.default()
intents.message_content = True   # needed to read '!' commands
intents.members = True           # needed for ctx.author.roles / member lookups
bot = commands.Bot(command_prefix='!', intents=intents, help_command=help_command)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@bot.check
async def globally_restrict_guild(ctx):
    if ctx.guild is not None:
        return str(ctx.guild.id) == ID
    return True  # allow DMs (leaderboard/stats/export rely on DMs)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        return  # silently ignore commands from the wrong guild
    logger.exception("Unhandled command error", exc_info=error)

@bot.command(name='tabloid', help='Tabloids another CNET. You must mention your victims.', aliases=["tb"])
async def add(ctx):
    if not ctx.message.attachments:
        await ctx.send(f"Please include your tabloid photo with your message.")
        return
    
    mentionsList = ctx.message.mentions
    perp = ctx.message.author
    
    if not mentionsList: 
        #list is empty
        await ctx.send(f"<@{perp.id}> Please mention your victim(s)!")
        return
    
    victims = []
    # try catch block here

    try:
        with sqlite3.connect(DATABASE) as conn:
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

    except sqlite3.Error as e:
        logger.exception("DB error in add()")
        await ctx.send("A database error occurred. Try again later.")
        return
    await ctx.message.add_reaction("📸")
    await benchmarks(perp, ctx)

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
            await user.send("You have reached " + str(record) + " tabloids!")

@bot.command(name='undo', help='Undo a tabloid.')
@commands.guild_only()
async def sub(ctx):
    if not ctx.message.mentions:
        await ctx.send(f"Make sure to mention your victim(s).")
        return

    if "section leader" in [role.name for role in ctx.author.roles] or "squid leaders" in [role.name for role in ctx.author.roles] or ctx.message.author == ctx.message.mentions[0]:
        # the perp is the first mention
        victims = []
        mentionsList = ctx.message.mentions[1:]
        perp = ctx.message.mentions[0]

    elif ctx.message.author != ctx.message.mentions[0]:
        # the perp is the author of the message
        victims = []
        mentionsList = ctx.message.mentions
        perp = ctx.message.author
    else:
        # someone is t
        await ctx.send(f"Please contact leadership to run this command.")
        return

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
    conn.close()
    await ctx.message.add_reaction("✅")
    #await ctx.send(f"Undid tabloid by {perp.display_name} for victims {', '.join(victims)}")


def embedrow(row, em):
        if row['name'] == "-" or row['name'] is None:
            em.add_field(name=f"**{row['discord_username']}**", value=f">>> Tabloids: {row['tabloids']}\nTimes Tabloided: {row['times_tabloided']}\nK/D Ratio: {row['kd']}",inline=False)
        else:
            em.add_field(name=f"**{row['name']}**", value=f">>> Tabloids: {row['tabloids']}\nTimes Tabloided: {row['times_tabloided']}\nK/D Ratio: {row['kd']}",inline=False)


#queries database and produces a leaderboard
#with different sortings, such as tabloids, tabloided, and k/d
@bot.command(name='leaderboard', help='Shows top 5 players and stats')
async def leaderboard(ctx, arg: str = commands.parameter(default="tabloids", description="tabloids, tabloided, or kd for various tables")):
    user = await bot.fetch_user(ctx.message.author.id)

    if ctx.guild is not None:
        await ctx.message.delete()
        await user.send("Please use the `leaderboard` command in a direct message with the bot to avoid spamming the server.")
        return

    conn = sqlite3.connect(DATABASE)
    query = """SELECT p.*, u.name FROM player_list p LEFT JOIN username_list u ON u.discord_username = p.discord_username"""
    df = pd.read_sql(query, conn)
    conn.close()

    if len(df) == 0:
        await user.send("Sorry, there's nothing to display yet.")
        return

    df['kd'] = round(df['tabloids'] / df['times_tabloided'], 2)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    sort_col = arg if arg in ("kd", "tabloids") else "times_tabloided"
    title = {"kd": "K/D Ratio Leaderboard", "tabloids": "Tabloids Leaderboard"}.get(arg, "Most Tabloided Leaderboard")

    df = df.sort_values(sort_col, ascending=False).head(5).fillna('-')

    embed = discord.Embed(title=title, color=0x00ff00)
    df.apply(embedrow, axis=1, em=embed)
    await user.send(embed=embed)


#whole leaderboard
@bot.command(name='global', help='Shows global statistics')
async def global_leaderboard(ctx):
    user = await bot.fetch_user(ctx.message.author.id)

    if ctx.guild is not None:
        await ctx.message.delete()
        await user.send("Please use the `global` command in a direct message with the bot to avoid spamming the server.")
        return

    conn = sqlite3.connect(DATABASE)
    query = """SELECT p.*, u.name FROM player_list p LEFT JOIN username_list u ON u.discord_username = p.discord_username"""
    df = pd.read_sql(query, conn)
    conn.close()

    if len(df) == 0:
        await user.send("Sorry, there's nothing to display yet.")
        return

    df['kd'] = round(df['tabloids'] / df['times_tabloided'], 2)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df = df.sort_values('tabloids', ascending=False).fillna('-')

    embeds = []
    for i in range(0, len(df), 5):
        embed = discord.Embed(title="Global Leaderboard", color=0x00ff00)
        df.iloc[i:i+5].apply(embedrow, axis=1, em=embed)
        embeds.append(embed)

    await my_paginator.Simple().start(ctx, pages=embeds, sendAsDM=True, user=user)

#provide stats for the user who called the command
@bot.command(name='stats', help='Shows your personal statistics')
async def stats(ctx):
    user = await bot.fetch_user(ctx.message.author.id)
    if(ctx.guild is not None):
        await ctx.message.delete()
        await user.send("Please use the `stats` command in a direct message with the bot to avoid spamming the server.")
        return
    conn = sqlite3.connect(DATABASE)
    query = "SELECT * from player_list WHERE discord_username = ?"
    df = pd.read_sql(query, conn, params=(ctx.message.author.name,))
    if(len(df) == 0):
        await user.send("Sorry, you don't have any stats to display yet!")
        return
    df['kd'] = round(df['tabloids']/df['times_tabloided'], 2)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df = df.fillna('-')
    conn.close()

    embed = discord.Embed(title=f"{ctx.message.author.name}'s stats", color=0x00ff00)
    df = df.head(1)
    embed.add_field(name=f"**Tabloids: {df['tabloids'][0]}**", value=f"**Times Tabloided: {df['times_tabloided'][0]}\nK/D Ratio: {df['kd'][0]}**",inline=False)
    await user.send(embed=embed)

@bot.command(name='name', help='Associate your name with your username')
#add text to the username list table
async def name(ctx, arg: str = commands.parameter(description="Your name")):
    perp = ctx.message.author
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO username_list (discord_username, name) VALUES (?, ?)""", (perp.name, arg))
    conn.commit()
    conn.close()
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
            return
    conn = sqlite3.connect(DATABASE)
    query = 'SELECT * from player_list'
    df = pd.read_sql(query, conn)
    conn.close()
    if(len(df) == 0):
        await user.send("Sorry, there's nothing to display yet.")
        return
    excel_file_path = 'exported_tabloid.xlsx'
    df.to_excel(excel_file_path, index=False)
    await user.send(file=discord.File(excel_file_path))
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
             tabloids INTEGER,
             times_tabloided INTEGER
             )""".format("player_list"))
    c.execute("""CREATE TABLE IF NOT EXISTS {} (
             discord_username string NOT NULL UNIQUE,
             name string NOT NULL
             )""".format("username_list"))
    conn.commit()
    conn.close()
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