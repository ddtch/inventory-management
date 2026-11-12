"""
Mock data for the Factory Inventory Management System
This module loads sample data from JSON files for inventory items, orders, demand forecasts, and backlog items.
All data is from September 2025 and includes warehouse, category, and date fields for filtering.
"""

import json
import os

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_json_file(filename):
    """Load data from a JSON file in the data directory"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

# Load all datasets from JSON files
inventory_items = load_json_file('inventory.json')
orders = load_json_file('orders.json')
demand_forecasts = load_json_file('demand_forecasts.json')
backlog_items = load_json_file('backlog_items.json')

# Load spending data
spending_data = load_json_file('spending.json')
spending_summary = spending_data['spending_summary']
monthly_spending = spending_data['monthly_spending']
category_spending = spending_data['category_spending']

# Load transactions
recent_transactions = load_json_file('transactions.json')

# Load purchase orders
purchase_orders = load_json_file('purchase_orders.json')

# Load user tasks shown in the header TasksModal
tasks = load_json_file('tasks.json')

# Restocking orders are the only dataset written at runtime. The file may be
# missing on a fresh checkout, so fall back to an empty list instead of failing.
RESTOCKING_ORDERS_FILE = os.path.join(DATA_DIR, 'restocking_orders.json')
restocking_orders = load_json_file('restocking_orders.json') if os.path.exists(RESTOCKING_ORDERS_FILE) else []


def save_restocking_orders():
    """Persist the in-memory restocking orders list to disk."""
    # Look the path up at call time (not import time) so tests can monkeypatch
    # RESTOCKING_ORDERS_FILE and never touch the real data file.
    target = RESTOCKING_ORDERS_FILE
    tmp_path = target + '.tmp'
    # Atomic write: dump to a temp file then os.replace, so a crash mid-write
    # never leaves a truncated JSON file that would break the next startup.
    with open(tmp_path, 'w') as f:
        json.dump(restocking_orders, f, indent=2)
        f.write('\n')
    os.replace(tmp_path, target)

# All data is now loaded from JSON files in the data/ directory
# This allows for easier maintenance and updates of the sample data
