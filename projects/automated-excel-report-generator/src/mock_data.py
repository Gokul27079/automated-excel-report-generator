import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_sales_data(num_rows=200, messy=True) -> pd.DataFrame:
    """
    Generates synthetic sales data for testing the pipeline.
    If messy=True, injects some duplicate Order IDs, null values, and casing inconsistencies.
    """
    products = {
        'Laptop': ('Electronics', 1200.00),
        'Smartphone': ('Electronics', 800.00),
        'Wireless Headphones': ('Accessories', 150.00),
        'Mechanical Keyboard': ('Accessories', 100.00),
        'Ergonomic Chair': ('Furniture', 350.00),
        'Desk Lamp': ('Furniture', 45.00),
        'Running Shoes': ('Apparel', 120.00),
        'Leather Jacket': ('Apparel', 250.00),
        'Smartwatch': ('Electronics', 220.00),
        'Backpack': ('Accessories', 65.00)
    }
    
    regions = ['North', 'South', 'East', 'West']
    
    data = []
    start_date = datetime(2026, 1, 1)
    
    for i in range(num_rows):
        order_id = f"ORD-{10000 + i}"
        date = start_date + timedelta(days=random.randint(0, 150))
        product_name = random.choice(list(products.keys()))
        category, unit_price = products[product_name]
        quantity = random.choice([1, 2, 3, 4, 5])
        revenue = quantity * unit_price
        region = random.choice(regions)
        
        row = {
            'Order ID': order_id,
            'Date': date.strftime('%Y-%m-%d'),
            'Product': product_name,
            'Category': category,
            'Quantity': quantity,
            'Unit Price': unit_price,
            'Revenue': revenue,
            'Region': region
        }
        data.append(row)
        
    df = pd.DataFrame(data)
    
    if messy:
        # Inject duplicates (approx 5%)
        dupe_indices = random.sample(range(num_rows), k=int(num_rows * 0.05))
        dupe_rows = df.iloc[dupe_indices].copy()
        # Modifying some values slightly so it's a true messy duplicate
        df = pd.concat([df, dupe_rows], ignore_index=True)
        
        # Inject null Order IDs (approx 2%)
        null_id_indices = random.sample(range(len(df)), k=int(len(df) * 0.02))
        df.loc[null_id_indices, 'Order ID'] = np.nan
        
        # Inject null Revenue values (approx 2%)
        null_rev_indices = random.sample(range(len(df)), k=int(len(df) * 0.02))
        df.loc[null_rev_indices, 'Revenue'] = np.nan
        
        # Inject trailing/leading whitespaces and mixed casings in categories and regions
        df['Region'] = df['Region'].apply(lambda x: f"  {x.lower()} " if isinstance(x, str) and random.random() < 0.3 else x)
        df['Product'] = df['Product'].apply(lambda x: x.upper() if isinstance(x, str) and random.random() < 0.2 else x)
        
    # Re-shuffle
    df = df.sample(frac=1).reset_index(drop=True)
    return df

def generate_mock_csv_string(num_rows=200, messy=True) -> str:
    """
    Generates synthetic sales data and returns it as a CSV-formatted string.
    """
    df = generate_mock_sales_data(num_rows, messy)
    return df.to_csv(index=False)
