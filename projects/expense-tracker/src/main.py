import os
import uvicorn
import logging

try:
    from src.database import init_db, get_all_expenses, seed_mock_data
except ImportError:
    from database import init_db, get_all_expenses, seed_mock_data

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("expense_tracker_main")

def start_server():
    logger.info("Initializing database...")
    init_db()
    
    # Auto-seed mock data on first run if database is empty
    try:
        current_data = get_all_expenses()
        if not current_data:
            logger.info("Database is empty. Seeding mock expenses for startup view...")
            seed_mock_data()
            logger.info("Mock expenses seeded successfully.")
    except Exception as e:
        logger.error(f"Failed to auto-seed mock data: {e}")
        
    logger.info("Starting uvicorn server for SpendWise Expense Tracker...")
    # Import app inside to ensure db initialization runs first
    try:
        from src.api import app
    except ImportError:
        from api import app
        
    # Start uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)

if __name__ == "__main__":
    start_server()
