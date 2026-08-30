import sqlite3
from datetime import datetime

DB_PATH = "shop.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            plan_name TEXT NOT NULL,
            price TEXT NOT NULL,
            receipt_file_id TEXT,
            config_link TEXT,
            status TEXT DEFAULT 'pending_payment', -- pending_payment, pending_config, completed, canceled
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_order(user_id: int, username: str, plan_name: str, price: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute('''
        INSERT INTO orders (user_id, username, plan_name, price, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, plan_name, price, now))
    
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    if order_id is None:
        raise ValueError("خطا در ثبت سفارش؛ شناسه سفارش تولید نشد.")
        
    return int(order_id)

def update_order_receipt(order_id: int, receipt_file_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders 
        SET receipt_file_id = ?, status = 'pending_config' 
        WHERE id = ?
    ''', (receipt_file_id, order_id))
    conn.commit()
    conn.close()

def set_order_completed(order_id: int, config_link: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders 
        SET config_link = ?, status = 'completed' 
        WHERE id = ?
    ''', (config_link, order_id))
    conn.commit()
    conn.close()

def get_order(order_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, username, plan_name, price, receipt_file_id, config_link, status FROM orders WHERE id = ?', (order_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_user_orders(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, plan_name, status, config_link FROM orders WHERE user_id = ? AND status = "completed"', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows