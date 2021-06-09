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
        self.schedule_notifcation()

    def schedule_notifcation(self):
        for time in self._notify_time_list:
            schedule.every().day.at(time).do(self.send_unfinished_cards_notifications)

    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def send_unfinished_cards_notifications(self):
        cards = self._trello_client.get_due_today_cards()
        for card in cards:
            self._bot.send_message(Notifier.card_obj_to_message(card))

    def card_obj_to_message(card: Card) -> str:
        return (f'{card.board.name}\n' +
                # f'{card.list.name}\n'  +
                f'{card.name}\n')


def flatten(src) -> Iterator:
    """flatten iterable of iterables"""
    return chain.from_iterable(src)


if __name__ == '__main__':
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    notifier = Notifier(config)
    notifier.run()