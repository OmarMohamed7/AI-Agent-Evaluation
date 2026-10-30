import sys

from psycopg import OperationalError

from agent.tools import purchase_history
from db.db import DB


def main():
    try:
        DB.query("SELECT 1")
    except (OperationalError, KeyError) as e:
        sys.exit(f"Could not connect to the database: {e}")

    print("Connected to the database.")
    print("Hello from agent-eval!")

    print(purchase_history("15"))


if __name__ == "__main__":
    main()
