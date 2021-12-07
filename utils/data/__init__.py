from contextlib import contextmanager
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
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
    def create_connection(cls):
        connection = cls.get_engine().begin()
        return connection

    @classmethod
    def get_engine(cls):
        if not cls.db:
            cls.connect_to_db()
        return cls.db

    @classmethod
    def insert(cls, **data):
        cls.get_table()
        with cls.db.begin() as connect:
            connect.execute(
                cls.table.insert(values=data)
            )

    @classmethod
    def update(cls, condition, **data):
        cls.get_table()
        with cls.db.begin() as connect:
            connect.execute(
                sa.update(cls.table).where(condition).values(**data)
            )

    @classmethod
    @contextmanager
    def do_with_session(cls):
        cls.get_engine()
        Session = sessionmaker(cls.db)
        session = Session()
        yield session
        session.commit()

    @classmethod
    def execute_with_session(cls, session, statement):
        result = session.execute(statement)
        return result

    @classmethod
    def get_data(cls, *fields, condition=None, limit: int = None, offset: int = None, order=None,) -> LegacyCursorResult:
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
