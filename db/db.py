import os
from typing import LiteralString

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()


class DB:
    _connection: psycopg.Connection | None = None

    @classmethod
    def get_connection(cls) -> psycopg.Connection:
        if cls._connection is None:
            cls._connection = psycopg.connect(os.environ["DATABASE_URL"], autocommit=True)
        return cls._connection

    @classmethod
    def query(cls, sql: LiteralString, params: tuple = ()) -> list[dict]:
        with cls.get_connection().cursor(row_factory=dict_row) as cur:
            return cur.execute(sql, params).fetchall()

    @classmethod
    def get_user(cls, user: str) -> dict | None:
        """Look a user up by numeric id or email."""
        rows = cls.query(
            'SELECT "Id", "Name", "Email" FROM "Users" WHERE "Id"::text = %s OR "Email" = %s',
            (user, user),
        )
        return rows[0] if rows else None

    @classmethod
    def get_user_orders(cls, user_id: int) -> list[dict]:
        return cls.query(
            '''
            SELECT o."Id" AS order_id, o."CreatedAt" AS date, o."Status" AS status,
                   i."ProductName" AS name, i."UnitPrice" AS price,
                   i."Quantity" AS quantity, i."TotalPrice" AS total_price
            FROM "Orders" o
            JOIN "OrderItems" i ON i."OrderId" = o."Id"
            WHERE o."UserId" = %s
            ORDER BY o."CreatedAt"
            ''',
            (user_id,),
        )
