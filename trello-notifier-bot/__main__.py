import os
import json
from argparse import ArgumentParser

from bot import TelegramBot


def main():
    """Launch bot using given config file given as parameter"""
    arg_parser = ArgumentParser()
    arg_parser.add_argument("config_file", type=str,
                            help="path to json file with config like example")
    args = arg_parser.parse_args()

    config_file_path = args.config_file
    if not os.path.isfile(config_file_path):
        print('You must give valid config file path')
        return

    with open(config_file_path, 'r') as config_file:
        try:
            config = json.load(config_file)
        except json.JSONDecodeError:
            print('You must provide valid json')
            return

    bot = TelegramBot(config)
    bot.start()

main()