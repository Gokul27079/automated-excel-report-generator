import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "expenses.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_all_expenses():
    """Retrieves all expense records sorted by date descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses ORDER BY date DESC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_expense_by_id(expense_id):
    """Retrieves a single expense record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_expense(amount, category, description, date_str):
    """Adds a new expense record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
        (float(amount), str(category).strip(), str(description).strip(), str(date_str).strip())
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_expense(expense_id, amount, category, description, date_str):
    """Updates an existing expense record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE expenses SET amount = ?, category = ?, description = ?, date = ? WHERE id = ?",
        (float(amount), str(category).strip(), str(description).strip(), str(date_str).strip(), int(expense_id))
    )
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def delete_expense(expense_id):
    """Deletes an expense record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def seed_mock_data():
    """Clears the table and seeds realistic mock expense data in Indian Rupees (INR)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses")
    
    mock_expenses = [
        # Food & Dining (INR values)
        (2500.00, "Food & Dining", "Grocery shopping at D-Mart", "2026-06-01"),
        (350.00, "Food & Dining", "Coffee and snacks at Café Coffee Day", "2026-06-02"),
        (4500.00, "Food & Dining", "Family weekend dinner at restaurant", "2026-06-05"),
        (450.00, "Food & Dining", "Swiggy lunch order takeout", "2026-06-08"),
        (3200.00, "Food & Dining", "Weekly fruits and veggies restock", "2026-06-12"),
        (250.00, "Food & Dining", "Breakfast tea & snacks", "2026-06-14"),
        
        # Transport (INR values)
        (3000.00, "Transport", "Gas station petrol refueling", "2026-06-02"),
        (450.00, "Transport", "Ola auto ride to office", "2026-06-04"),
        (1500.00, "Transport", "Monthly local train transit pass", "2026-06-06"),
        (200.00, "Transport", "Metro parking fee", "2026-06-10"),
        (2800.00, "Transport", "Gas station petrol refueling", "2026-06-13"),
        
        # Utilities (INR values)
        (3200.00, "Utilities", "Electricity bill (TNEB/BESCOM)", "2026-06-01"),
        (500.00, "Utilities", "Water utility bill", "2026-06-01"),
        (999.00, "Utilities", "JioFiber broadband internet subscription", "2026-06-03"),
        (719.00, "Utilities", "Airtel mobile prepaid recharge", "2026-06-05"),
        
        # Entertainment (INR values)
        (649.00, "Entertainment", "Netflix Premium monthly subscription", "2026-06-01"),
        (119.00, "Entertainment", "Spotify Premium monthly music", "2026-06-01"),
        (1200.00, "Entertainment", "PVR movie tickets & popcorn", "2026-06-06"),
        (6500.00, "Entertainment", "Concert ticket booking", "2026-06-10"),
        (850.00, "Entertainment", "Bowling & arcade games with friends", "2026-06-11"),
        
        # Housing (INR values)
        (22000.00, "Housing", "Monthly house rent payment", "2026-06-01"),
        (3500.00, "Housing", "Society maintenance charges", "2026-06-02"),
        (1200.00, "Housing", "Home cleaning supplies", "2026-06-07"),
        
        # Health & Wellness (INR values)
        (1500.00, "Health & Wellness", "Monthly gym subscription", "2026-06-01"),
        (850.00, "Health & Wellness", "Apollo Pharmacy medicine refill", "2026-06-04"),
        (2500.00, "Health & Wellness", "Doctor consultation & checkup fee", "2026-06-09"),
        
        # Miscellaneous (INR values)
        (450.00, "Miscellaneous", "Stationery supplies", "2026-06-03"),
        (3500.00, "Miscellaneous", "Birthday gift for family member", "2026-06-07"),
        (1000.00, "Miscellaneous", "Donation to local NGO", "2026-06-12")
    ]
    
    cursor.executemany(
        "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
        mock_expenses
    )
    conn.commit()
    conn.close()
