import json
import time
import datetime
from itertools import chain
from typing import List, Iterator

import telegram
import schedule
from trello import TrelloClient, Card


class MyTrelloClient:
    _client: TrelloClient
    def __init__(self, trello_api_keys: dict):
        self._client = TrelloClient(**trello_api_keys)
    
    def get_due_today_cards(self) -> List[Card]:
        """returns card, what have due date what is today or before and is not closed"""
        boards = self._client.list_boards()
        cards = flatten(map(lambda board: board.open_cards(), boards))
        cards = filter(lambda card: card.due is not None, cards)
        cards = filter(lambda card: not card.is_due_complete , cards)
        date_today = datetime.date.today()
        cards = filter(lambda card: card.due_date.date() <= date_today,
                       cards)
        cards = list(cards)
        return cards


class MyTelgramBot:
    _bot: telegram.Bot
    _owner_chat_id: str
    def __init__(self, telegram_config: dict):
        self._bot = telegram.Bot(telegram_config['bot_token'])
        self._owner_chat_id = telegram_config['owner_chat_id']

    def send_message(self, text):
        self._bot.send_message(self._owner_chat_id, text)


class Notifier:
    _trello_client: MyTrelloClient
    _bot: MyTelgramBot
    _notify_time_list: List[str]
    def __init__(self, config: dict):
        self._trello_client = MyTrelloClient(config['trello_api_keys'])
        self._bot = MyTelgramBot(config['telegram'])
        self._notify_time_list = config['notification_times']
        self._set_up_notification_times()

    def start(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def _set_up_notification_times(self):
        for time in self._notify_time_list:
            schedule.every().day.at(time).do(self._send_messages_with_unfinished_cards)


    def _send_messages_with_unfinished_cards(self):
        cards = self._trello_client.get_due_today_cards()
        for card in cards:
            self._bot.send_message(text=Notifier.card_obj_to_message(card))

    def card_obj_to_message(card: Card) -> str:
        return (f'{card.due_date.strftime("%m.%d")}\n'  +
                f'{card.name}\n')


def flatten(src) -> Iterator:
    """flatten iterable of iterables"""
    return chain.from_iterable(src)


def main():
    """Launch bot using given config file given as parameter"""
    import os
    from argparse import ArgumentParser

    arg_parser = ArgumentParser()
    arg_parser.add_argument("config_file", type=str,
                            help="path to json file with config like example")
    args = arg_parser.parse_args()

    config_file_path = args.config_file
    if not os.path.isfile(config_file_path):
        print('You must give valid file path')
        return

    with open(config_file_path, 'r') as config_file:
        try:
            config = json.load(config_file)
        except json.JSONDecodeError:
            print('You must provide valid json')
            return

    notifier = Notifier(config)
    notifier.start()


if __name__ == '__main__':
    main()

