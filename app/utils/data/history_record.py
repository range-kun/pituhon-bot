from __future__ import annotations

import re

import sqlalchemy as sa
from sqlalchemy.engine import Row
from sqlalchemy.sql import extract
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList

from app.configuration import MAX_HIST_RETRIEVE_RECORDS
from app.log import logger
from app.utils.data import Data


class HistoryRecord(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "history_record",
            cls.metadata,
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("date", sa.DATE),
            sa.Column("log", sa.TEXT),
        )

    @classmethod
    def parse_date(cls, text: str) -> list[int] | None:
        date = re.match(r"((?:\d{2}-)?(?:\d{2}-)?\d{4})", text)
        if not date:
            return
        return [int(i) for i in date[1].split("-")[::-1]]

    @classmethod
    def format_condition(cls, date: list[int]) -> BinaryExpression | BooleanClauseList:
        if len(date) == 3:  # full date
            date = "-".join(str(i) for i in date)
            return cls.get_table().c.date == date

        date_field = cls.get_table().c["date"]
        if len(date) == 2:  # year and month
            year, month = date
            return (extract("year", date_field) == year) & (extract("month", date_field) == month)
        if len(date) == 1:  # only year
            year = date[0]
            return extract("year", date_field) == year

    @classmethod
    def get_record(cls, date: str = None, offset: int | None = None) -> list | str:
        if not date:
            return cls.get_random_record()

        date = cls.parse_date(date)
        limit = None
        if offset:
            offset = max(0, offset)
            limit = MAX_HIST_RETRIEVE_RECORDS
        try:
            result = cls.get_data(
                "date",
                "log",
                limit=limit,
                offset=offset,
                condition=(cls.format_condition(date)),
                order=cls.table.c.date,
            )
        except Exception as e:
            logger.opt(exception=True).error(
                f"Exception occurred {str(e)} while fetching data from Data Base",
            )
            return "Извините произошла ошибка при попытке достать фразу"

        result = result.fetchall()
        if (query_len := len(result)) > MAX_HIST_RETRIEVE_RECORDS:
            return (
                f"Всего за указанный период было найдено {query_len} записей."
                f" Что бы не засорять чат, "
                f"могу показать не более {MAX_HIST_RETRIEVE_RECORDS} записей за один раз. "
                f"Пожалуйста укажите номер записи с которой начать -> rec 2021 5"
            )
        return result or "На указанную дату записей не найдено"

    @classmethod
    def get_random_record(cls) -> list[Row] | str:
        try:
            record = cls.get_data("date", "log", limit=1, order=sa.func.random()).fetchall()
        except Exception as e:
            logger.opt(exception=True).error(
                f"Exception occurred {str(e)} while fetching data from Data Base",
            )
            return "Извините не удалось получить фразу"
        return record
