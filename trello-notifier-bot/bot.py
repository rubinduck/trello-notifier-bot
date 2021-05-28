import json
import datetime
from itertools import chain
from typing import List, Iterator

import telegram
from trello import TrelloClient, Card


class MyTrelloClient:
    def __init__(self, trello_api_keys: dict):
        self._client = TrelloClient(**trello_api_keys)
    
    def get_due_today_cards(self) -> List[Card]:
        boards = self._client.list_boards()
        cards = flatten(map(lambda board: board.open_cards(), boards))
        cards = filter(lambda card: card.due is not None, cards)
        # date_today = datetime.date.today()
        date_today = datetime.date(2021, 2, 22)
        cards = filter(lambda card: card.due_date.date() == date_today,
                       cards)
        return cards


def flatten(src) -> Iterator:
    """flatten iterable of iterables"""
    return chain.from_iterable(src)


class MyTelgramBot:
    def __init__(self, telegram_config: dict):
        self._bot = telegram.Bot(telegram_config['bot_token'])
        self.owner_chat_id = telegram_config['owner_chat_id']

    def send_message(self, text):
        self._bot.send_message(self.owner_chat_id, text)


if __name__ == '__main__':
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    my_client = MyTrelloClient(config['trello_api_keys'])
    my_telegram_bot = MyTelgramBot(config['telegram'])
    my_telegram_bot.send_message('test')