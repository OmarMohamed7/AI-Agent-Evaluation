import os
from typing import LiteralString

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()


class _AlreadyRefunded(Exception):
    pass


class DB:
    _connection: psycopg.Connection | None = None
    _schema_ready = False

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

    @classmethod
    def ensure_schema(cls) -> None:
        """Create the agent-owned tables (the rest of the schema belongs to the API)."""
        if cls._schema_ready:
            return
        cls.get_connection().execute(
            '''
            CREATE TABLE IF NOT EXISTS "RefundTickets" (
                "Id" SERIAL PRIMARY KEY,
                "UserId" INTEGER NOT NULL,
                "OrderId" INTEGER NOT NULL,
                "ProductName" TEXT NOT NULL,
                "RefundAmount" NUMERIC(12, 2) NOT NULL,
                "CreatedAt" TIMESTAMPTZ NOT NULL DEFAULT now(),
                UNIQUE ("UserId", "OrderId", "ProductName")
            )
            '''
        )
        cls._schema_ready = True

    @classmethod
    def create_refund_tickets(
        cls, user_id: int, lines: list[tuple[int, str, float]]
    ) -> bool:
        """Insert one ticket per (order_id, product_name, amount) line, atomically.

        Returns False (and inserts nothing) if any line was already refunded; the
        unique constraint makes this safe against concurrent requests too.
        """
        cls.ensure_schema()
        try:
            with cls.get_connection().transaction(), cls.get_connection().cursor() as cur:
                for order_id, name, amount in lines:
                    cur.execute(
                        'INSERT INTO "RefundTickets" ("UserId","OrderId","ProductName","RefundAmount") '
                        "VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                        (user_id, order_id, name, amount),
                    )
                    if cur.rowcount == 0:
                        raise _AlreadyRefunded
        except _AlreadyRefunded:
            return False
        return True
