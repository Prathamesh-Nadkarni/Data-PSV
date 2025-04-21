import sqlite3
import pandas as pd
import os


def connection(db_path):
    """Create a connection to the SQLite database"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(base_dir, '..', 'Data', 'sqllite-db')

    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    db_path = os.path.join(db_dir, db_path)
    conn = sqlite3.connect(db_path)

    return conn

def fetch_sales_by_product(product_name):
    conn = connection("sales_data.db")
    query = """
        SELECT * FROM sales
        WHERE [product_name] = ?
    """
    df = pd.read_sql_query(query, conn, params=(product_name,))
    conn.close()
    return df


def fetch_all_product_names():
    query = """
        SELECT DISTINCT product_name FROM sales
        ORDER BY product_name
    """
    conn = connection("sales_data.db")
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df




def fetch_sales_by_category(product_category):
    conn = connection("sales_data.db")
    query = """
        SELECT * FROM sales
        WHERE [product_category] = ?
    """
    df = pd.read_sql_query(query, conn, params=(product_category,))
    conn.close()
    return df