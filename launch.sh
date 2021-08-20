#!/bin/bash
# move to script location
program_name="trello-notifier-bot"
config_path="config.yaml"
cd "$(dirname "$0")"
# kill bot if it is running
pkill --full "python $program_name"
# set up venv
if [ -d "venv" ]; then
	rm -r venv
fi
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# if config file path is not passed, use default name
if [ ! -z "$1" ]; then
	config_path="$1"
fi
python "$program_name" "$config_path" &
