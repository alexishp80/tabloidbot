# reset.py
import os
import sqlite3
from dotenv import load_dotenv
from dotenv import set_key
from datetime import datetime
import logging

# setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()
DATABASE = os.getenv('DATABASE')

logging.info(f"Resolved absolute path: {os.path.abspath(DATABASE)}")


try:
    # drop table
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""DROP TABLE IF EXISTS player_list""")
    conn.commit()
    c.close()
    conn.close()
    logging.info("Dropped player_list table")


    # rename file
    new_filename = f"cnets{datetime.now().year%100}.db"
    os.rename(os.path.abspath(DATABASE), new_filename)

    # update .env
    set_key(".env", "DATABASE", new_filename)
    logging.info("Environment variable updated")

except sqlite3.Error as e:
    logging.error(f"SQLite error: {e}")
except FileNotFoundError as e:
    logging.error(f"File error: {e}")
except Exception as e:
    logging.error(f"An unexpected error occurred: {e}")