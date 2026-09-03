# CNET Tabloid Bot
The CNET Tabloid Bot is a simple Discord bot that is used to keep track of the CNET tabloid. It is used to tabloid another CNET and display both personal and global statistics.

Usage documentation can be found [here](https://github.com/alexishp80/tabloidbot/blob/main/docs/usage.md).

### Setup
The application requires sensitive environment variables. If you want to stand up your own version, you must create your own application using the [Discord Developer Portal](https://discord.com/developers). 

Requires: Python >=3.8 
```zsh
% git clone https://github.com/alexishp80/tabloidbot.git
% cd tabloid bot
% python3 -m venv .venv
% source .venv/bin/activate
```

Within the environment, install the dependencies from requirements.txt
```
pip install -r requirements.txt
```
Then, run the app
```
python3 bot.py
``` 

Alternatively, you can run the bot as a service.

```
#/etc/systemd/system/tabloid.service

[Unit]
Description=Boot Script for Tabloid Bot
After=multi-user.target

[Service]
Type=simple
Restart=always
WorkingDirectory=git_repo_root_path
ExecStart=/usr/bin/python3 git_repo_root_path/bot.py
User=apaul

[Install]
WantedBy=multi-user.target
```
