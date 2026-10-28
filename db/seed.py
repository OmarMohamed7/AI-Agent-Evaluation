"""Seed the Ecommerce DB with random users, and the orders/items they purchased.

Usage: uv run python -m db.seed [--users 10] [--max-orders 4] [--seed 42]
"""
import argparse
import base64
import hashlib
import os
import random
import struct
from datetime import datetime, timedelta, timezone

from db.db import DB

FIRST = [
    "Omar", "Sara", "Ahmed", "Laila", "John", "Emma", "Youssef", "Mona", "Liam", "Nora", "Karim", "Hana",
    "Mohamed", "Fatma", "Mostafa", "Aya", "Tarek", "Dina", "Khaled", "Salma", "Ali", "Rana", "Hossam", "Yara",
    "Noah", "Olivia", "Lucas", "Sophia", "Ethan", "Mia", "Daniel", "Chloe", "Adam", "Zoe", "Ryan", "Lena",
]
LAST = [
    "Hassan", "Ali", "Smith", "Ibrahim", "Johnson", "Mahmoud", "Brown", "Saleh", "Khan", "Adel",
    "Mohamed", "Farouk", "Nasser", "Soliman", "Fathy", "Mansour", "Gomaa", "Zaki", "Williams", "Jones",
    "Garcia", "Miller", "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Moore", "Martin", "Lee",
]
DEFAULT_PRODUCTS = [
    ("Laptop", "A Gaming Laptop", 50000.00, 25),
    ("Headphone", "A Gaming Headphone", 5000.00, 50),
    ("Playstation 3", "A good playstation 3 with original controllers", 7000.00, 20),
    ("Iphone 17", "256 GB, 98% Battery Percentage, and mobile overall in a excellent state", 55000.00, 5),
    ("Wireless Charger", "15 Watt wireless charger for Iphone", 993.80, 100),
    ("Mechanical Keyboard", "RGB mechanical keyboard with blue switches", 2500.00, 60),
    ("Gaming Mouse", "Wireless gaming mouse, 16000 DPI", 1800.00, 80),
    ("27 Inch Monitor", "27 inch 144Hz QHD IPS monitor", 12000.00, 30),
    ("Bluetooth Speaker", "Portable waterproof Bluetooth speaker", 1500.00, 70),
    ("Smart Watch", "Fitness smart watch with heart-rate and GPS", 6500.00, 40),
    ("Tablet", "10.5 inch tablet, 128 GB storage", 14000.00, 25),
    ("Webcam", "1080p webcam with built-in microphone", 1200.00, 90),
    ("Wifi Router", "Dual-band AC1200 wifi router", 1100.00, 55),
    ("External SSD 1TB", "Portable 1 TB USB-C solid state drive", 4200.00, 45),
    ("Power Bank", "20000 mAh fast-charging power bank", 900.00, 120),
    ("USB-C Hub", "7-in-1 USB-C hub with HDMI and card reader", 750.00, 85),
    ("Xbox Controller", "Wireless controller for Xbox and PC", 2300.00, 50),
    ("Office Chair", "Ergonomic office chair with lumbar support", 8500.00, 15),
    ("Phone Case", "Shockproof case for Iphone", 250.00, 200),
    ("Camera", "24 MP mirrorless camera with 18-55mm lens", 38000.00, 8),
]
STATUSES = [0, 1, 2, 3]
DEFAULT_PASSWORD = "123456789"


def hash_password(password: str) -> str:
    """ASP.NET Core Identity v3 hash (HMAC-SHA512, 100k iterations), as the API stores them."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha512", password.encode(), salt, 100_000, 32)
    return base64.b64encode(b"\x01" + struct.pack(">III", 2, 100_000, len(salt)) + salt + key).decode()


def seed(n_users: int, max_orders: int) -> None:
    conn = DB.get_connection()
    now = datetime.now(timezone.utc)
    with conn.transaction(), conn.cursor() as cur:
        cur.execute('SELECT "Name" FROM "Products"')
        existing = {r[0] for r in cur.fetchall()}
        cur.executemany(
            'INSERT INTO "Products" ("Name","Description","Price","Stock","CreatedAt") VALUES (%s,%s,%s,%s,%s)',
            [(*p, now) for p in DEFAULT_PRODUCTS if p[0] not in existing],
        )
        cur.execute('SELECT "Id","Name","Price" FROM "Products"')
        products = cur.fetchall()

        for _ in range(n_users):
            first, last = random.choice(FIRST), random.choice(LAST)
            email = f"{first}.{last}.{random.randint(1000, 999999)}@example.com".lower()
            created = now - timedelta(days=random.randint(180, 365))
            cur.execute(
                'INSERT INTO "Users" ("Name","Email","PasswordHash","Role","CreatedAt") '
                "VALUES (%s,%s,%s,'USER',%s) RETURNING \"Id\"",
                (f"{first} {last}", email, hash_password(DEFAULT_PASSWORD), created),
            )
            user_id = cur.fetchone()[0] # type: ignore

            for _ in range(random.randint(0, max_orders)):
                order_date = now - timedelta(seconds=random.randint(0, 180 * 86400))
                items = [(pid, name, price, random.randint(1, 3))
                         for pid, name, price in random.sample(products, random.randint(1, min(3, len(products))))]
                cur.execute(
                    'INSERT INTO "Orders" ("UserId","CreatedAt","Status","TotalPrice","Quantity") '
                    'VALUES (%s,%s,%s,%s,%s) RETURNING "Id"',
                    (user_id, order_date, random.choice(STATUSES),
                     sum(p * q for _, _, p, q in items), sum(q for *_, q in items)),
                )
                order_id = cur.fetchone()[0] # type: ignore
                cur.executemany(
                    'INSERT INTO "OrderItems" ("OrderId","ProductId","ProductName","Quantity","UnitPrice") '
                    "VALUES (%s,%s,%s,%s,%s)",
                    [(order_id, pid, name, q, price) for pid, name, price, q in items],
                )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=10)
    ap.add_argument("--max-orders", type=int, default=4)
    ap.add_argument("--seed", type=int, default=None, help="make the random data reproducible")
    args = ap.parse_args()
    random.seed(args.seed)
    seed(args.users, args.max_orders)
    print(f"Seeded {args.users} users (up to {args.max_orders} orders each).")
