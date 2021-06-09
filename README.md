# trello-notifier-bot
Telegram bot sending messages about trello cards deadlines

# How it works
Every day at times given in config bot sends messages about cards with deadline today or before

# How to launch
1. Copy example of config file
2. Add your trello api key and and api secret
3. Add your telegram bot api key and your chat id (can get from @chatid_echo_bot or simular bot)
4. Add times of day you want resive notification
5. Create venv and install dependencies
```console
python -m venv venv
source venv/bin/activate on unix
venv\Scripts\activate.bat on Windows
pip install -r requirements.txt
```
6. Launch app with ```python bot.py path_to_config_file.json```