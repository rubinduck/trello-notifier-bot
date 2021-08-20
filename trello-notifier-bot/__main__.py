import os
import yaml
from typing import Optional
from argparse import ArgumentParser

from bot import TelegramBot

def validate_config(config: dict, config_template: dict):
    """
    checks if given loaded from yaml config matches template
    if not throws exception with reason
    """
    if config.keys() != config_template.keys():
        raise ValidationException(
            f'Config dont have {set(config_template.keys()) - set(config.keys())} keys')
    for key in config_template:
        config_value = config[key]
        template_value = config_template[key]
        if type(config_value) != type(template_value):
            raise ValidationException(
                f'Key "{key}" must have type [{type(template_value)}] but have [{type(config_value)}]')
        elif type(config_value) == dict:
            validate_config(config_value, template_value)

class ValidationException(Exception):
    def __init__(self, message):
        self.message = message

def main():
    """Launch bot using given config file given as parameter"""
    arg_parser = ArgumentParser()
    arg_parser.add_argument("config_file", type=str,
                            help="path to yaml file with config like example")
    args = arg_parser.parse_args()

    config_file_path = args.config_file
    if not os.path.isfile(config_file_path):
        print('You must give valid config file path')
        return

    with open(config_file_path, 'r') as config_file:
        try:
            config = yaml.safe_load(config_file)
        except yaml.YAMLError:
            print('File you provided has incorrect yaml')
            return
    with open('example-config.yaml', 'r') as file:
        config_template = yaml.safe_load(file)
    try:
        validate_config(config, config_template)
    except ValidationException as ex:
        print('Provided config file dont match example one:')
        print(ex.message)
        return

    bot = TelegramBot(config)
    bot.start()

main()