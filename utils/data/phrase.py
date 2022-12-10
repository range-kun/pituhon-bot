from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.engine import Row

from utils.data import Data


class PhraseData(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "phrase",
            cls.metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("author", sa.TEXT),
            sa.Column("text", sa.TEXT)
        )

    @classmethod
    def get_random_phrase(cls) -> str | list[Row]:
        try:
            phrase = cls.get_data("author", "text", limit=1, order=sa.func.random()).fetchone()
        except Exception as e:
            print(e)
            return "Извините не удалось получить фразу"
        return phrase
