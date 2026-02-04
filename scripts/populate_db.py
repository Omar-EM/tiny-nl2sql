"""Populate the project's Postgres database from the ecommerce CSV dataset.

This script is idempotent: it drops and recreates tables, then bulk loads
CSV files from the repository `dataset/ecommerce_dataset/` folder using
Postgres COPY (fast). It expects a running Postgres instance reachable via
environment variables or the default shown below.

Usage (from project root):
  python scripts/populate_db.py
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

load_dotenv(override=True)


DATA_DIR = Path(__file__).resolve().parents[1] / "dataset" / "ecommerce_dataset"


def get_conn():
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    dbname = os.getenv("PGDATABASE", "postgres")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "")
    conn_str = f"host={host} port={port} dbname={dbname} user={user}"
    if password:
        conn_str += f" password={password}"
    return psycopg2.connect(conn_str)


def create_tables(cur):
    cur.execute("DROP TABLE IF EXISTS events")
    cur.execute("DROP TABLE IF EXISTS reviews")
    cur.execute("DROP TABLE IF EXISTS order_items")
    cur.execute("DROP TABLE IF EXISTS orders")
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("DROP TABLE IF EXISTS users")
    # TODO Should gender be enum ?
    cur.execute(
        """
        CREATE TABLE users (
            user_id varchar PRIMARY KEY,
            name text,
            email text,
            gender varchar,
            city text,
            signup_date date
        );

        CREATE TABLE products (
            product_id varchar PRIMARY KEY,
            product_name text,
            category text,
            brand text,
            price numeric,
            rating numeric
        );

        CREATE TABLE orders (
            order_id varchar PRIMARY KEY,
            user_id varchar REFERENCES users(user_id),
            order_date timestamptz,
            order_status varchar,
            total_amount numeric
        );

        CREATE TABLE order_items (
            order_item_id varchar PRIMARY KEY,
            order_id varchar REFERENCES orders(order_id),
            product_id varchar REFERENCES products(product_id),
            user_id varchar REFERENCES users(user_id),
            quantity integer,
            item_price numeric,
            item_total numeric
        );

        CREATE TABLE reviews (
            review_id varchar PRIMARY KEY,
            order_id varchar REFERENCES orders(order_id),
            product_id varchar REFERENCES products(product_id),
            user_id varchar REFERENCES users(user_id),
            rating integer,
            review_text text,
            review_date timestamptz
        );

        CREATE TABLE events (
            event_id varchar PRIMARY KEY,
            user_id varchar REFERENCES users(user_id),
            product_id varchar REFERENCES products(product_id),
            event_type varchar,
            event_timestamp timestamptz
        );
        """
    )


def load_csv_copy(cur, table: str, csv_path: Path, columns=None):
    """Use COPY to load CSV file into `table`. `columns` is optional list."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    cols_sql = (
        sql.SQL(",").join(sql.Identifier(c) for c in columns)
        if columns
        else sql.SQL("")
    )
    if columns:
        copy_sql = sql.SQL("COPY {}({}) FROM STDIN WITH CSV HEADER").format(
            sql.Identifier(table), cols_sql
        )
    else:
        copy_sql = sql.SQL("COPY {} FROM STDIN WITH CSV HEADER").format(
            sql.Identifier(table)
        )
    with csv_path.open("r", encoding="utf-8") as f:
        cur.copy_expert(copy_sql.as_string(cur), f)


def main():
    print(f"Using dataset directory: {DATA_DIR}")
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                print("Creating tables...")
                create_tables(cur)

                print("Loading users.csv -> users")
                load_csv_copy(cur, "users", DATA_DIR / "users.csv")

                print("Loading products.csv -> products")
                load_csv_copy(cur, "products", DATA_DIR / "products.csv")

                print("Loading orders.csv -> orders")
                load_csv_copy(cur, "orders", DATA_DIR / "orders.csv")

                print("Loading order_items.csv -> order_items")
                load_csv_copy(cur, "order_items", DATA_DIR / "order_items.csv")

                print("Loading reviews.csv -> reviews")
                load_csv_copy(cur, "reviews", DATA_DIR / "reviews.csv")

                print("Loading events.csv -> events")
                load_csv_copy(cur, "events", DATA_DIR / "events.csv")

        print("Data load complete. Committed to database.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
