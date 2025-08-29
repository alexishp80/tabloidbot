# Tabloid Bot Usage

## Discord Bot Overview
Discord bots are automated programs that can add additional functionality to a server. You can interact with bots by typing specific commands in the chat, which triggers the bot to perform the desired action. You can use `!help` to recieve a list of all the commands and their function. From there, you can use `!help [command]` to recieve detailed information on a specific command. 

## Tabloid Bot Commands
`!name`: The bot uses your Discord username as an identifier in the database. To make displaying the statistics friendlier, you can use this command to associate your preferred name with your username, and it will appear in the stats and leaderboard commands.

`!tabloid` or `!tb`: This is how you will tabloid others. You must send a photo with this command and you must mention at least one person in the photo. The bot will react with :camera: when your tabloid has been processed. 

`!undo`: If your tabloid does not follow the rules (e.g., they saw you before you sent it) you can acknowledge your mistake and use the `!undo` command to remove this entry from the database. You must mention your victim. Leadership also has the ability to undo a tabloid, by using `!undo @tabloider @victim`. The bot will react with :white_check_mark: when the tabloid has been removed. 

`!stats`: This command is used to see your personal statistics, like number of tabloids, times tabloided, and your K/D ratio (times you have tabloided someone divided by times you have been tabloided.)

`!leaderboard`: This shows the top 5 players along with their stats. The default is sorting by K/D, but you can also use `!leaderboard tabloids` or `!leaderboard tabloided` to sort by those respective values. 

`!global`: This shows a global leaderboard with every player. Since the list is so long, the results need to be broken up into pages. 

`!export`: This will produce an Excel spreadsheet of the underlying database. 

The `!stats`, `!leaderboard`, and `!global` commands must be used in a direct message with the bot. 

## Discord Bot Implementation
The source code for this bot is available [here](https://github.com/alexishp80/tabloidbot). It's a simple implementation written in Python, and runs on a headless Raspberry Pi Zero sitting in my living room. If you're interested in maintaining/running this in the future, reach out to me on Discord [@tenderbread](https://discordapp.com/users/tenderbread). It would be more of a headache to run on campus, but some cursory research has led me to believe it's doable. 