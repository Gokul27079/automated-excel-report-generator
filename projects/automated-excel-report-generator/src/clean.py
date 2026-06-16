import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw sales data:
    - Normalizes column headers to standard names (Order ID, Date, Product, Revenue, Region)
    - Removes rows where Order ID or Revenue is null
    - Removes duplicate Order IDs
    - Converts Date column to datetime
    - Standardizes text columns (strips whitespace, applies title case)
    """
    cleaned_df = df.copy()
    
    # 1. Normalize column names to match expected headers
    col_mapping = {}
    for col in cleaned_df.columns:
        col_lower = str(col).strip().lower().replace("_", " ").replace("-", " ")
        if col_lower in ['order id', 'orderid', 'id', 'transaction id']:
            col_mapping[col] = 'Order ID'
        elif col_lower in ['date', 'order date', 'transaction date', 'created at']:
            col_mapping[col] = 'Date'
        elif col_lower in ['revenue', 'sales', 'total sales', 'total revenue', 'amount']:
            col_mapping[col] = 'Revenue'
        elif col_lower in ['product', 'item', 'product name', 'item name']:
            col_mapping[col] = 'Product'
        elif col_lower in ['region', 'territory', 'location']:
            col_mapping[col] = 'Region'
        elif col_lower in ['category', 'product category']:
            col_mapping[col] = 'Category'
        elif col_lower in ['quantity', 'qty', 'units']:
            col_mapping[col] = 'Quantity'
        elif col_lower in ['unit price', 'price', 'rate']:
            col_mapping[col] = 'Unit Price'
            
    cleaned_df.rename(columns=col_mapping, inplace=True)
    
    # Check if critical columns are present
    required_cols = ['Order ID', 'Date', 'Revenue']
    missing_cols = [col for col in required_cols if col not in cleaned_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in CSV: {', '.join(missing_cols)}. Please verify headers.")
    
    # Ensure other expected columns exist, if not, create placeholder/empty ones
    optional_cols = {
        'Product': 'Unknown Product',
        'Region': 'Unknown Region',
        'Category': 'General',
        'Quantity': 1,
        'Unit Price': cleaned_df['Revenue'] if 'Revenue' in cleaned_df.columns else 0.0
    }
    for col, default_val in optional_cols.items():
        if col not in cleaned_df.columns:
            if col == 'Unit Price' and isinstance(default_val, pd.Series):
                cleaned_df[col] = default_val
            else:
                cleaned_df[col] = default_val

    # 2. Clean nulls
    # Remove rows where Order ID or Revenue is null
    initial_rows = len(cleaned_df)
    cleaned_df.dropna(subset=['Order ID', 'Revenue'], inplace=True)
    null_rows_removed = initial_rows - len(cleaned_df)
    if null_rows_removed > 0:
        logger.info(f"Removed {null_rows_removed} rows with null Order ID or Revenue.")
        
    # Fill remaining nulls in text columns with default values
    for col in ['Product', 'Region', 'Category']:
        cleaned_df[col] = cleaned_df[col].fillna(optional_cols[col])
    
    # 3. Remove duplicate Order IDs (keep first)
    pre_dupes_rows = len(cleaned_df)
    # Ensure Order ID is treated as string/standardized before checking duplicates
    cleaned_df['Order ID'] = cleaned_df['Order ID'].astype(str).str.strip()
    cleaned_df.drop_duplicates(subset=['Order ID'], keep='first', inplace=True)
    dupe_rows_removed = pre_dupes_rows - len(cleaned_df)
    if dupe_rows_removed > 0:
        logger.info(f"Removed {dupe_rows_removed} duplicate Order ID rows.")
        
    # 4. Convert Date column to datetime format
    try:
        cleaned_df['Date'] = pd.to_datetime(cleaned_df['Date'], errors='coerce')
        # Drop rows where date could not be parsed
        invalid_dates = cleaned_df['Date'].isna().sum()
        if invalid_dates > 0:
            cleaned_df.dropna(subset=['Date'], inplace=True)
            logger.info(f"Removed {invalid_dates} rows with invalid dates.")
    except Exception as e:
        logger.error(f"Error parsing dates: {e}")
        raise ValueError(f"Error parsing dates column: {e}")
        
    # 5. Standardize text columns (strip whitespace, title case)
    for col in ['Product', 'Region', 'Category']:
        cleaned_df[col] = cleaned_df[col].astype(str).str.strip().str.title()
        
    # 6. Ensure correct numeric types
    cleaned_df['Revenue'] = pd.to_numeric(cleaned_df['Revenue'], errors='coerce').fillna(0.0)
    cleaned_df['Quantity'] = pd.to_numeric(cleaned_df['Quantity'], errors='coerce').fillna(1).astype(int)
    cleaned_df['Unit Price'] = pd.to_numeric(cleaned_df['Unit Price'], errors='coerce').fillna(0.0)
    
    logger.info(f"Data cleaning complete. {len(cleaned_df)} rows remaining.")
    return cleaned_df
