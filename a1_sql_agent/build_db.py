import os
import random
import sqlite3
from datetime import date, timedelta

RANDOM_SEED = 42


def build_database(db_path="data.db"):
    """Build a deterministic SQLite database for the SQL agent assignment."""
    random.seed(RANDOM_SEED)

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                signup_date TEXT NOT NULL
            );
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL
            );
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );
            CREATE TABLE order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            """
        )

        cities = ["Dhaka", "Chittagong", "Khulna", "Rajshahi", "Sylhet", "Barishal"]
        first_names = [
            "Amina", "Rahim", "Karim", "Nadia", "Sabbir", "Farhana", "Imran",
            "Tania", "Rafi", "Mitu", "Hasan", "Lamia", "Jamal", "Rina", "Omar",
        ]
        last_names = [
            "Islam", "Ahmed", "Khan", "Rahman", "Hossain", "Chowdhury", "Ali",
            "Sarkar", "Das", "Uddin",
        ]
        start_signup = date(2022, 1, 1)
        customers = []
        for i in range(1, 61):  # 60 customers
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            city = random.choice(cities)
            signup = start_signup + timedelta(days=random.randint(0, 900))
            customers.append((i, name, city, signup.isoformat()))
        cur.executemany(
            "INSERT INTO customers(id, name, city, signup_date) VALUES (?, ?, ?, ?)",
            customers,
        )

        categories = ["Electronics", "Books", "Grocery", "Home", "Clothing"]
        adjectives = ["Basic", "Premium", "Eco", "Compact", "Deluxe", "Smart", "Classic"]
        nouns = ["Lamp", "Notebook", "Rice", "Mixer", "Shirt", "Headset", "Bag", "Bottle", "Pen", "Chair"]
        products = []
        for i in range(1, 51):  # 50 products
            name = f"{random.choice(adjectives)} {random.choice(nouns)} {i}"
            category = random.choice(categories)
            price = round(random.uniform(5.0, 500.0), 2)
            products.append((i, name, category, price))
        cur.executemany(
            "INSERT INTO products(id, name, category, price) VALUES (?, ?, ?, ?)",
            products,
        )

        statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
        start_order = date(2023, 1, 1)
        orders = []
        for i in range(1, 241):  # 240 orders
            customer_id = random.randint(1, 60)
            order_dt = start_order + timedelta(days=random.randint(0, 700))
            status = random.choices(statuses, weights=[1, 3, 2, 3, 1], k=1)[0]
            orders.append((i, customer_id, order_dt.isoformat(), status))
        cur.executemany(
            "INSERT INTO orders(id, customer_id, order_date, status) VALUES (?, ?, ?, ?)",
            orders,
        )

        price_by_id = {p[0]: p[3] for p in products}
        order_items = []
        item_id = 1
        for order_id in range(1, 241):
            n_items = random.randint(1, 4)  # ensures >=240, target >=500
            used_products = set()
            for _ in range(n_items):
                product_id = random.randint(1, 50)
                # allow repeats across attempts but keep (order,product) varied reasonably
                tries = 0
                while product_id in used_products and tries < 5:
                    product_id = random.randint(1, 50)
                    tries += 1
                used_products.add(product_id)
                quantity = random.randint(1, 5)
                unit_price = price_by_id[product_id]
                order_items.append((item_id, order_id, product_id, quantity, unit_price))
                item_id += 1
        # guarantee >= 500 items
        while len(order_items) < 500:
            order_id = random.randint(1, 240)
            product_id = random.randint(1, 50)
            quantity = random.randint(1, 5)
            unit_price = price_by_id[product_id]
            order_items.append((item_id, order_id, product_id, quantity, unit_price))
            item_id += 1

        cur.executemany(
            "INSERT INTO order_items(id, order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
            order_items,
        )

        conn.commit()
    finally:
        conn.close()

    return db_path


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "data.db")
    build_database(path)
    print(f"Built database at {path}")
