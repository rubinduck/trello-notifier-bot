import json
import time
import datetime
from enum import Enum
from itertools import chain
from threading import Thread
from typing import List, Iterator, Optional

import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (CallbackQueryHandler, ConversationHandler,
CommandHandler)
from telegram import ext as tg_ext
import schedule
from trello import TrelloClient, Card

class State(Enum):
    CHOOSING_BOARD = 0
    CHOOSING_LIST  = 1

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
        self._add_handlers()

    def _add_handlers(self) -> State:
        conversation_handler = ConversationHandler(
            entry_points=[CommandHandler('add', self._handle_add)],
            states={
                State.CHOOSING_BOARD: [CallbackQueryHandler(self._handle_choose_board)],
                State.CHOOSING_LIST: [CallbackQueryHandler(self._handle_choose_list)]
            },
            fallbacks=[CommandHandler('cancel', self._handle_cancel)]
        )
        self._updater.dispatcher.add_handler(conversation_handler)

        callback_query_handler = CallbackQueryHandler(self._handle_callback_query)
        self._updater.dispatcher.add_handler(callback_query_handler)

    def _handle_cancel(self, update: telegram.Update, context: tg_ext.CallbackContext):
        self._bot.send_message(update.message.chat_id, 'Canceled')
        return ConversationHandler.END

    def _handle_add(self, update: telegram.Update, context: tg_ext.CallbackContext):
        if len(context.args) < 2:
            self._bot.send_message(update.message.chat_id, 'Your message must include date and name')
            return ConversationHandler.END
        # TODO a bit clumpsi None returning func, think how to rewrite
        date = context.args[0]
        date = to_date_if_correct(date)
        if date is None:
            self._bot.send_message(update.message.chat_id, 'Incorrect date')
            return ConversationHandler.END
        card_name = ''.join(context.args[1:])
        context.user_data['date'] = date
        context.user_data['card-name'] = card_name

        boards = self._trello_client.list_boards()
        reply_button_rows = []
        for board in boards:
            callback_data = self._prepare_callback_data(act='choose-add-board', data=board.id)
            reply_button_rows.append([InlineKeyboardButton(board.name, callback_data=callback_data)])
        reply_markup = InlineKeyboardMarkup(reply_button_rows)
        self._bot.send_message(chat_id=update.message.chat_id,
                               text='Choose board',
                               reply_markup=reply_markup)
        return State.CHOOSING_BOARD

    def _handle_choose_board(self, update: telegram.Update, context: tg_ext.CallbackContext):
        query = update.callback_query
        callback_data = json.loads(query.data)
        act = callback_data['act']
        act_data = callback_data['data']
        query.answer()
        if act != 'choose-add-board':
            self._bot.send_message('Finish or cancle adding new car before doing something else')
            return
        board_id = act_data
        reply_keyboard = self._gen_choose_list_inline_keyboard(board_id)
        query.edit_message_text('Choose list')
        query.edit_message_reply_markup(reply_markup=reply_keyboard)
        return State.CHOOSING_LIST

    def _gen_choose_list_inline_keyboard(self, board_id: str) -> InlineKeyboardMarkup:
        board = self._trello_client.get_board(board_id)
        board_lists = board.all_lists()
        reply_button_rows = []
        for board_list in board_lists:
            callback_data = self._prepare_callback_data(act='choose-add-list', data=board_list.id)
            reply_button_rows.append([InlineKeyboardButton(board_list.name, callback_data=callback_data)])
        return InlineKeyboardMarkup(reply_button_rows)

    def _handle_choose_list(self, update: telegram.Update, context: tg_ext.CallbackContext):
        query = update.callback_query
        callback_data = json.loads(query.data)
        act = callback_data['act']
        act_data = callback_data['data']
        query.answer()
        query.edit_message_reply_markup(reply_markup=None)
        if act != 'choose-add-list':
            self._bot.send_message('Finish or cancle adding new car before doing something else')
            return
        list_id = act_data
        user_data = context.user_data
        _list = self._trello_client.get_list(list_id)
        card_due_date = user_data['date'].isoformat()
        card_name = user_data['card-name']
        _list.add_card(card_name, due=card_due_date)
        query.edit_message_text('Done ✅')
        return ConversationHandler.END

    def _prepare_callback_data(self, act: str, data: str):
        """
        combined length of callback_data must be <= 64 bytes
        json dict takes 21 simbol, so 43 lefts for act and data
        """
        callback_data = json.dumps({'act': act, 'data': data})
        if len(callback_data) > 64:
            raise Exception(f'United length of act and data is too big ({len(callback_data)}).For more info watch method)')
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
            # schedule.every(5).seconds.do(self._send_messages_with_unfinished_cards)

    def _handle_callback_query(self, update: telegram.Update, context: tg_ext.CallbackContext):
        query = update.callback_query
        query.answer()
        callback_data = json.loads(query.data)
        act = callback_data['act']
        act_data = callback_data['data']
        if act != 'mark-finished':
            self._bot.send_message(query.message.chat_id, 'Unavalible command now')
            return
        card_id = act_data
        card = self._trello_client.get_card(card_id)
        card.set_due_complete()
        query.answer()
        new_message_text = query.message.text + '\nDone ✅'
        query.edit_message_text(new_message_text)


    def _send_messages_with_unfinished_cards(self):
        cards = self._get_due_today_cards()
        for card in cards:
            msg_text = TelegramBot.card_obj_to_message_text(card)
            callback_data = self._prepare_callback_data(act='mark-finished', data=card.id)
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

def to_date_if_correct(date: str) -> Optional[datetime.datetime]:
    try:
        day, month, year = date.split('.')
        date = datetime.datetime(int(year), int(month), int(day))
    except ValueError:
        return None
    return date

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