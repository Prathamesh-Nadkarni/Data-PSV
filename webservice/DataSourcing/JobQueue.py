import threading
import queue
import time
import random
import sqlite3
import os
from uuid import uuid4

# ---- Database Setup ----

def connection(db_path):
    """Create a connection to the SQLite database"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(base_dir, '..', 'Data', 'sqllite-db')
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    db_path = os.path.join(db_dir, db_path)
    conn = sqlite3.connect(db_path)

    return conn

def insert_sales(country, category, product_name, sales, quantity):
    conn = connection('sales_data.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO sales (country, category, product_name, sales, quantity)
        VALUES (?, ?, ?, ?, ?)
    ''', (country, category, product_name, sales, quantity))
    conn.commit()
    conn.close()

def get_sales_by_product_name(product_name):
    conn = connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, country, category, product_name, sales, quantity
        FROM sales
        WHERE product_name = ?
        LIMIT 1
    ''', (product_name,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "country": row[1],
            "category": row[2],
            "product_name": row[3],
            "sales": row[4],
            "quantity": row[5]
        }
    return None

def update_sales_by_product_name(product_name, country=None, category=None, sales=None, quantity=None):
    conn = connection()
    cur = conn.cursor()
    # Build dynamic SQL for only provided fields
    fields = []
    values = []
    if country is not None:
        fields.append("country = ?")
        values.append(country)
    if category is not None:
        fields.append("category = ?")
        values.append(category)
    if sales is not None:
        fields.append("sales = ?")
        values.append(sales)
    if quantity is not None:
        fields.append("quantity = ?")
        values.append(quantity)
    if not fields:
        conn.close()
        return False  # Nothing to update
    values.append(product_name)
    sql = f"UPDATE sales SET {', '.join(fields)} WHERE product_name = ?"
    cur.execute(sql, values)
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated


# ---- Job Queue Implementation ----

class SalesJob:
    def __init__(self, country, category, product_name, sales, quantity):
        self.id = str(uuid4())
        self.status = "pending"
        self.data = {
            "country": country,
            "category": category,
            "product_name": product_name,
            "sales": sales,
            "quantity": quantity
        }

class JobQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.jobs = {}
        self.lock = threading.Lock()
        self.worker = threading.Thread(target=self.worker_loop, daemon=True)
        self.worker.start()

    def submit_job(self, country, category, product_name, sales, quantity):
        job = SalesJob(country, category, product_name, sales, quantity)
        with self.lock:
            self.jobs[job.id] = job
        self.queue.put(job)
        return job.id

    def get_status(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                return job.status
            return "not found"

    def worker_loop(self):
        while True:
            job = self.queue.get()
            # Simulate pending -> in progress
            with self.lock:
                job.status = "in progress"
            time.sleep(random.randint(5, 10))  # Simulate processing delay

            # Simulate data fetch and insert into DB
            insert_sales(**job.data)
            with self.lock:
                job.status = "completed"
            self.queue.task_done()

# ---- API-like Functions ----

# Initialize the database and job queue (singleton style)
job_queue = JobQueue()

def submit_sales_job(country, category, product_name, sales, quantity):
    """
    Simulates an API endpoint to submit a sales data job.
    Returns a job_id.
    """
    return job_queue.submit_job(country, category, product_name, sales, quantity)


def get_job_status(job_id):
    """
    Simulates an API endpoint to check job status.
    Returns "pending", "in progress", "completed", or "not found".
    """
    return job_queue.get_status(job_id)

# ---- Example Usage ----

if __name__ == "__main__":
    # Submit a job
    job_id = submit_sales_job("USA", "Electronics", "Tablet", 3500.0, 12)
    print(f"Submitted job {job_id}")

    # Poll for status
    while True:
        status = get_job_status(job_id)
        print(f"Job status: {status}")
        if status == "completed":
            print("Job finished and data inserted into DB!")
            break
        time.sleep(2)
    print("Exiting...")