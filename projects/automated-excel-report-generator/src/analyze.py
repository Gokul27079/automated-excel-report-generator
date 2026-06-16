import pandas as pd
import logging

logger = logging.getLogger(__name__)

def run_analysis(df: pd.DataFrame) -> dict:
    """
    Analyzes the cleaned DataFrame and returns a dictionary of:
    - kpis: dict with total_revenue, total_orders, average_order_value
    - top_products: DataFrame (Top 10 Products by Revenue)
    - monthly_trends: DataFrame (Monthly Revenue Trend)
    - regional_sales: DataFrame (Region-wise Sales Breakdown with revenue share %)
    """
    if df.empty:
        raise ValueError("Cannot analyze empty DataFrame.")

    # 1. KPI Row calculations
    total_revenue = float(df['Revenue'].sum())
    total_orders = int(df['Order ID'].nunique())
    average_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0.0
    
    kpis = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'average_order_value': average_order_value
    }
    
    # 2. Top 10 Products by Revenue
    top_products = (
        df.groupby('Product')
        .agg(
            Revenue=('Revenue', 'sum'),
            Quantity_Sold=('Quantity', 'sum'),
            Orders=('Order ID', 'count')
        )
        .sort_values(by='Revenue', ascending=False)
        .head(10)
        .reset_index()
    )
    
    # 3. Monthly Revenue Trend
    # Create a Month-Year sortable key and label
    df_temp = df.copy()
    df_temp['YearMonth'] = df_temp['Date'].dt.to_period('M')
    
    monthly_trends = (
        df_temp.groupby('YearMonth')
        .agg(
            Revenue=('Revenue', 'sum'),
            Orders=('Order ID', 'count'),
            Quantity_Sold=('Quantity', 'sum')
        )
        .sort_index()
        .reset_index()
    )
    # Convert Period to string format YYYY-MM
    monthly_trends['Month'] = monthly_trends['YearMonth'].astype(str)
    monthly_trends.drop(columns=['YearMonth'], inplace=True)
    # Reorder columns to put Month first
    monthly_trends = monthly_trends[['Month', 'Revenue', 'Orders', 'Quantity_Sold']]
    
    # 4. Region-wise Sales Breakdown
    regional_sales = (
        df.groupby('Region')
        .agg(
            Revenue=('Revenue', 'sum'),
            Orders=('Order ID', 'count')
        )
        .sort_values(by='Revenue', ascending=False)
        .reset_index()
    )
    # Add Revenue Share %
    regional_sales['Revenue Share %'] = (regional_sales['Revenue'] / total_revenue * 100).round(2) if total_revenue > 0 else 0.0

    logger.info("Analysis successfully completed.")
    return {
        'kpis': kpis,
        'top_products': top_products,
        'monthly_trends': monthly_trends,
        'regional_sales': regional_sales
    }
