from typing import Optional

import sqlalchemy as sa
from sqlalchemy.engine.cursor import LegacyCursorResult

from configuration import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD


class Data:
    table: Optional[sa.sql.schema.Table] = None
    db: Optional[sa.engine.Engine] = None

    @classmethod
    def get_table(cls) -> sa.Table:
        if not cls.db:
            cls.connect_to_db()
            cls.table = cls.create_table()
        return cls.table

    @classmethod
    def create_table(cls):
        pass

    @classmethod
    def connect_to_db(cls):
        cls.db = sa.create_engine(
            url=f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}'
        )

    @classmethod
    def insert(cls, **data):
        cls.get_table()
        with cls.db.connect() as connect:
            connect.execute(
                cls.table.insert(values=data)
            )

    @classmethod
    def get_data(cls, *fields, condition=None, limit: int = None, offset: int = None, order=None) -> LegacyCursorResult:
        fields = [cls.get_table().c[field] for field in fields]
        query = sa.select(*fields)
        if condition is not None:
            query = query.where(condition)
        if order is not None:
            query = query.order_by(order)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        with cls.db.begin() as connect:
            result = connect.execute(
                query
            )

        return result
