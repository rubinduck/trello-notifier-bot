# trello-notifier-bot
Telegram bot sending messages about trello cards deadlines
Requires python 3.9+

# How it works
Every day at times given in config bot sends messages about cards with deadline today or before

# How to launch
1. Copy example of config file
2. Add your trello api key and and api secret
3. Add your telegram bot api key and your chat id (can get from @chatid_echo_bot or simular bot)
4. Add times of day you want resive notification
5. launch bot using `$./launch.sh <config_file_path_relative_to_script>`. If you dont pass config
file name it will be config.yaml
6. If you dont want use script manually install dependencies and run `$python trello-notifier-bot <config-file-path>`
