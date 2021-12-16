import sqlalchemy as sa

from utils.data import Data


class MaxStatsForPeriod(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "max_server_messages_for_period",
            sa.MetaData(),
            sa.Column("period", sa.VARCHAR),
            sa.Column("date", sa.DATE),
            sa.Column("amount", sa.INTEGER)
        )

    @classmethod
    def get_max_stats_for_period(cls, period):
        try:
            result = cls.get_data("amount", condition=(cls.get_table().c.period == period))

        except Exception as e:
            print(e)
            return "Извините произошла ошибка при попытке получить данных о сервере"

        result = result.fetchone()
        return result

    @classmethod
    def update_max_stats(cls, period, amount):
        cls.update(condition=(cls.get_table().c.period == period), amount=amount)


class MaxServerMessagesForPeriod(MaxStatsForPeriod):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "max_server_messages_for_period",
            sa.MetaData(),
            sa.Column("period", sa.VARCHAR),
            sa.Column("date", sa.DATE),
            sa.Column("amount", sa.INTEGER)
        )


class MaxServerSymbolsForPeriod(MaxStatsForPeriod):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "max_server_symbols_for_period",
            sa.MetaData(),
            sa.Column("period", sa.VARCHAR),
            sa.Column("date", sa.DATE),
            sa.Column("amount", sa.INTEGER)
        )
