import sqlalchemy as sa
from sqlalchemy.engine import Row

from app.utils import tomorrow_text_type
from app.utils.data import Data


class BirthdayDataReminder(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_birthday",
            cls.metadata,
            sa.Column("user_id", sa.BIGINT, primary_key=True),
            sa.Column("date", sa.DATE),
        )

    @classmethod
    def get_birthdays_for_next_day(cls):
        result = cls.get_data(
            "user_id",
            condition=(cls.get_table().c.date == tomorrow_text_type()),
        )
        result = result.fetchall()
        return result or None

    @classmethod
    def get_all_birthday_users(cls) -> list[Row]:
        result = cls.get_data("user_id", "date")
        return result.fetchall()

    @classmethod
    def get_user_birth_day(cls, user_id: int) -> str | None:
        result = cls.get_data(
            "date",
            condition=(cls.get_table().c.user_id == user_id),
        )
        result = result.fetchone()
        if result:
            return result[0].strftime("%Y-%m-%d")

    @classmethod
    def is_user_in_db(cls, user_id: int) -> bool:
        return bool(
            BirthdayDataReminder.get_data(
                "user_id",
                condition=(BirthdayDataReminder.get_table().c.user_id == user_id)
            ).first()
        )
