from contextlib import contextmanager
from typing import Callable, Optional

import sqlalchemy as sa
from sqlalchemy.engine.cursor import LegacyCursorResult
from sqlalchemy.orm import sessionmaker

from app.configuration import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

metadata = sa.MetaData()


class Data:
    table: Optional[sa.Table] = None
    db: Optional[sa.engine.Engine] = None
    metadata = metadata

    @classmethod
    def get_table(cls) -> sa.Table:
        if not cls.db:
            cls.connect_to_db()
        if cls.table is None:
            cls.table = cls.create_table()
        return cls.table

    @classmethod
    def create_table(cls):
        pass

    @classmethod
    def connect_to_db(cls):
        cls.db = sa.create_engine(
            url=f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        )

    @classmethod
    def create_connection(cls):
        connection = cls.get_engine().begin()
        return connection

    @classmethod
    def get_engine(cls):
        if not cls.db:
            cls.connect_to_db()
        return cls.db

    @classmethod
    def insert(
        cls,
        *,
        connection=None,
        **data,
    ):
        cls.get_table()
        cls.execute(statement=lambda: cls.table.insert(values=data), connection=connection)

    @classmethod
    def update(cls, *, connection=None, condition=None, **data):
        cls.get_table()
        query = sa.update(cls.table)
        if condition is not None:
            query = query.where(condition)
        cls.execute(statement=lambda: query.values(**data), connection=connection)

    @classmethod
    def delete(cls, *, connection=None, condition=None):
        cls.get_table()
        query = sa.delete(cls.table)
        if condition is not None:
            query = query.where(condition)
        cls.execute(statement=lambda: query, connection=connection)

    @classmethod
    def begin(cls):
        return cls.get_engine().begin()

    @classmethod
    @contextmanager
    def do_with_session(cls):
        cls.get_engine()
        Session = sessionmaker(cls.db)  # noqa N806
        session = Session()
        yield session
        session.commit()

    @classmethod
    def get_data(
        cls,
        *fields,
        condition=None,
        limit: int = None,
        offset: int = None,
        order=None,
        connection=None,
    ) -> LegacyCursorResult:
        table = cls.get_table()
        fields = [table.c[field] for field in fields]
        query = sa.select(*fields)

        if condition is not None:
            query = query.where(condition)
        if order is not None:
            query = query.order_by(order)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        result = cls.execute(statement=lambda: query, connection=connection)

        return result

    @classmethod
    def delete_all_table_data(cls, connection=None):
        cls.get_table()
        cls.execute(statement=lambda: sa.delete(cls.table), connection=connection)

    @classmethod
    def execute(cls, *, statement: Callable, connection=None):
        if connection is not None:
            result = connection.execute(statement())
        else:
            with cls.db.begin() as connect:
                result = connect.execute(statement())

        return result
