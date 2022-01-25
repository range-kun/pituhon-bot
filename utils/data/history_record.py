from __future__ import annotations

from typing import Union, Optional
import re

import sqlalchemy as sa
from sqlalchemy.sql import extract

from configuration import MAX_HIST_RETRIEVE_RECORDS
from utils.data import Data


class HistoryRecord(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "history_record",
            sa.MetaData(),
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("date", sa.DATE),
            sa.Column("log", sa.TEXT)
        )

    @classmethod
    def parse_date(cls, text: str):
        date = re.match(r'((?:\d{2}-)?(?:\d{2}-)?\d{4})', text)
        if not date:
            return
        return [int(i) for i in date[1].split('-')[::-1]]

    @classmethod
    def format_condition(cls, date):
        if len(date) == 3:  # full date
            date = '-'.join(str(i) for i in date)
            return cls.get_table().c.date == date

        date_field = cls.get_table().c["date"]
        if len(date) == 2:  # year and month
            year, month = date
            return (extract("year", date_field) == year) \
                & (extract("month", date_field) == month)
        if len(date) == 1:  # only year
            year = date[0]
            return extract("year", date_field) == year

    @classmethod
    def get_record(cls, text: str = None, offset: Optional[str] = None) -> Union[list, str]:
        if not text:
            record = cls.get_random_record()
            return record

        date = cls.parse_date(text)
        limit = None
        if offset:
            if offset.isdigit():
                offset = max(0, int(offset) - 1)
                limit = MAX_HIST_RETRIEVE_RECORDS
            else:
                return "Пожалуйста укажите номер записи в числовом виде: -> rec 2021 5"

        try:
            result = cls.get_data("date",
                                  "log",
                                  limit=limit,
                                  offset=offset,
                                  condition=(cls.format_condition(date)),
                                  order=cls.table.c.date
                                  )
        except Exception as e:
            print(e)
            return "Извините произошла ошибка при попытке достать фразу"

        result = result.fetchall()
        if (query_len := len(result)) > MAX_HIST_RETRIEVE_RECORDS:
            return f"Всего за указанный период было найдено {query_len} записей. Что бы не засорять чат, " \
                   f"могу показать не более {MAX_HIST_RETRIEVE_RECORDS} записей за один раз. " \
                   f"Пожалуйста укажите номер записи с которой начать -> rec 2021 5"
        return result or "На указанную дату записей не найдено"

    @classmethod
    def get_random_record(cls) -> str:
        try:
            record = cls.get_data("date", "log", limit=1, order=sa.func.random()).fetchall()
        except Exception as e:
            print(e)
            return 'Извините не удалось получить фразу'
        return record
