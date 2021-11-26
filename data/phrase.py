import sqlalchemy as sa

from data import Data


class PhraseData(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "phrase",
            sa.MetaData(),
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("author", sa.TEXT),
            sa.Column("text", sa.TEXT)
        )

    @classmethod
    def get_random_phrase(cls) -> str:
        try:
            phrase = cls.get_data("author", "text", limit=1, order=sa.func.random()).fetchone()
        except Exception as e:
            print(e)
            return 'Извините не удалось получить фразу'
        return phrase
