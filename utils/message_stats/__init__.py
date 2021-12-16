from __future__ import annotations

import re
from typing import Type
from types import SimpleNamespace

import sqlalchemy as sa
from sqlalchemy import func

from configuration import PYTHON_BOT_ID
from utils.data import Data
from utils.data.user_stats import UserStatsForCurrentMonth, UserStatsForCurrentWeek


class UserStatsForCurrentDay(SimpleNamespace):
    amount_of_symbols: int = 0
    amount_of_messages: int = 0


class MessageCounter:
    messages: int = 0
    symbols: int = 0
    authors: dict[int, UserStatsForCurrentDay] = {}

    @classmethod
    def set_stats_to_zero(cls):
        cls.messages = 0
        cls.symbols = 0
        cls.authors = {}

    @classmethod
    def proceed_message_info(cls, message):
        msg = message.content.lower()
        if message.author.id == PYTHON_BOT_ID:
            return

        cls.messages += 1
        sticker_regex = re.compile(r'<:\w+:\d+>')
        if sticker_regex.search(msg):
            number_of_symbols_in_string = 1
            cls.symbols += 1
        else:
            number_of_symbols_in_string = len(msg.replace(' ', ''))
            cls.symbols += len(msg.replace(' ', ''))

        user_stats = cls.authors.get(message.author.id, UserStatsForCurrentDay())
        user_stats.amount_of_messages = user_stats.amount_of_messages + 1
        user_stats.amount_of_symbols = user_stats.amount_of_symbols + number_of_symbols_in_string
        cls.authors[message.author.id] = user_stats

    @classmethod
    def get_server_stats_for_day(cls):
        user_id_with_most_messages = max(cls.authors, key=lambda user: cls.authors[user].amount_of_messages)
        user_with_most_messages = cls.authors[user_id_with_most_messages].amount_of_messages

        user_id_with_most_symbols = max(cls.authors, key=lambda user: cls.authors[user].amount_of_symbols)
        user_with_most_symbols = cls.authors[user_id_with_most_symbols].amount_of_symbols
        return [(user_id_with_most_messages, user_with_most_messages),
                (user_id_with_most_symbols, user_with_most_symbols)
                ]

    @classmethod
    def get_server_stats_for_week(cls) -> list:
        table = UserStatsForCurrentWeek.get_table()
        return cls.get_stats_for_period(table, UserStatsForCurrentWeek)

    @classmethod
    def get_server_stats_for_month(cls) -> list:
        table = UserStatsForCurrentMonth.get_table()
        return cls.get_stats_for_period(table, UserStatsForCurrentMonth)

    @classmethod
    def get_stats_for_period(cls, table: sa.Table, data_class: Type[Data]) -> list:
        message_field = table.c["messages"]
        symbol_field = table.c["symbols"]
        user_id_field = table.c["user_id"]

        with data_class.do_with_session() as session:
            channel_info = session.query(func.sum(message_field),
                                         func.sum(symbol_field))
            user_with_most_messages_info = \
                session.query(user_id_field,
                              message_field).order_by(sa.desc(message_field)).limit(1)
            user_with_most_symbols_info = \
                session.query(user_id_field,
                              symbol_field).order_by(sa.desc(symbol_field)).limit(1)

        return [channel_info.first(),
                user_with_most_messages_info.all()[0],
                user_with_most_symbols_info.all()[0]
                ]


class Statistic:
    bot = None

    @classmethod
    def set_bot(cls, bot):
        cls.bot = bot
