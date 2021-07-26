import json
import time
import datetime
from itertools import chain
from threading import Thread
from typing import List, Iterator

import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ext as tg_ext
import schedule
from trello import TrelloClient, Card



class TelegramBot:
    # _bot: telegram.Bot
    # _notifier: Notifier
    # _trello_client: MyTrelloClient
    # _updater: telegram.ext.Updater
    # _owner_id: str
    # TODO somehow verify config is right
    def __init__(self, config:dict):
        self._bot              = telegram.Bot(config['telegram']['bot_token'])
        self._updater          = tg_ext.Updater(config['telegram']['bot_token'])
        self._owner_id         = config['telegram']['owner_chat_id']
        self._trello_client    = TrelloClient(**config['trello_api_keys'])
        self._notify_time_list = config['notification_times']

        self._set_up_notification_schedule(self._notify_time_list)
        self._add_callback_query_handler()


    def _prepare_callback_data(self, act: str, data: str):
        """
        combined length of callback_data must be <= 64 bytes
        json dict takes 21 simbol, so 43 lefts for act and data
        """
        callback_data = json.dumps({'act': act, 'data': data})
        if len(callback_data) > 64:
            raise Exception('United length of act and data is too big (watch method)')
        return callback_data
    def start(self):
        self._start_notifing()
        self._start_handling_messages()

    def _start_notifing(self):
        def run_scheduler():
            import threading
            while True:
                schedule.run_pending()
                time.sleep(1)
        thread = Thread(target=run_scheduler, daemon=True)
        thread.start()

    def _start_handling_messages(self):
        self._updater.start_polling()
        self._updater.idle()

    def _set_up_notification_schedule(self, notification_times: List[str]):
        for time in notification_times:
            schedule.every().day.at(time).do(self._send_messages_with_unfinished_cards)

    def _add_callback_query_handler(self):
        callback_query_handler = tg_ext.CallbackQueryHandler(self._handle_callback_query)
        self._updater.dispatcher.add_handler(callback_query_handler)

    def _handle_callback_query(self, update: telegram.Update, context: tg_ext.CallbackContext):
        query = update.callback_query
        callback_data = json.loads(query.data)
        if callback_data['act'] == 'mark-card-finished':
            card_id = callback_data['data']
            card = self._trello_client.get_card(card_id)
            card.set_due_complete()
            query.answer()
            new_message_text = query.message.text + '\nDone ✅'
            query.edit_message_text(new_message_text)
        else:
            query.answer()
            query.edit_message_text('Unknow callback command. May be server issue')


    def _send_messages_with_unfinished_cards(self):
        cards = self._get_due_today_cards()
        for card in cards:
            msg_text = TelegramBot.card_obj_to_message_text(card)
            callback_data = self._prepare_callback_data(act='mark-card-finished', data=card.id)
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton('Finished', callback_data=callback_data)]])
            self._bot.send_message(text=msg_text,
                                   chat_id=self._owner_id,
                                   reply_markup=reply_markup)

    # TODO maybe rename
    def _get_due_today_cards(self) -> List[str]:
        """returns string card representations,
           what have due date what is today or before and is not closed"""
        boards = self._trello_client.list_boards()
        cards = flatten(map(lambda board: board.open_cards(), boards))
        cards = filter(lambda card: card.due is not None, cards)
        cards = filter(lambda card: not card.is_due_complete , cards)
        date_today = datetime.date.today()
        cards = filter(lambda card: card.due_date.date() <= date_today,
                       cards)
        return list(cards)

    def card_obj_to_message_text(card: Card) -> str:
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

    bot = TelegramBot(config)
    bot.start()


if __name__ == '__main__':
    main()