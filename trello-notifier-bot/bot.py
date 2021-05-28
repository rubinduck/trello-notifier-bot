import json
import datetime
from itertools import chain
from typing import List, Iterator

from trello import TrelloClient, Card


class MyTrelloClient:
    def __init__(self, acces_keys: dict):
        self._client = TrelloClient(**client_acces_keys)
    
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

if __name__ == '__main__':
    with open('config.json', 'r') as config_file:
        client_acces_keys = json.load(config_file)
    my_client = MyTrelloClient(client_acces_keys)
    print(list(my_client.get_due_today_cards()))