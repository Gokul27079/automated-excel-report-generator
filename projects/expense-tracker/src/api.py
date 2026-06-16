import os
import io
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from src.database import (
        init_db, get_all_expenses, get_expense_by_id, 
        add_expense, update_expense, delete_expense, seed_mock_data
    )
    from src.excel_exporter import export_expenses_to_excel
except ImportError:
    from database import (
        init_db, get_all_expenses, get_expense_by_id, 
        add_expense, update_expense, delete_expense, seed_mock_data
    )
    from excel_exporter import export_expenses_to_excel

# Initialize database on startup
init_db()

app = FastAPI(
    title="AI-Powered Expense Tracker API",
    description="REST API to manage expenses, perform visual analytics, and export formatted Excel sheets."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schema for new / updated expenses
class ExpenseSchema(BaseModel):
    amount: float = Field(..., gt=0, description="Amount spent")
    category: str = Field(..., description="Expense category (e.g. Food, Transport)")
    description: str = Field(None, description="Optional description")
    date: str = Field(..., description="Date of transaction (YYYY-MM-DD)")

@app.get("/api/expenses")
async def get_expenses():
    """Retrieve all expenses."""
    try:
        return get_all_expenses()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/expenses")
async def create_expense(expense: ExpenseSchema):
    """Add a new expense."""
    try:
        new_id = add_expense(
            amount=expense.amount,
            category=expense.category,
            description=expense.description or "",
            date_str=expense.date
        )
        return {"status": "success", "id": new_id, "message": "Expense created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/expenses/{expense_id}")
async def edit_expense(expense_id: int, expense: ExpenseSchema):
    """Update an existing expense by ID."""
    try:
        exists = get_expense_by_id(expense_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Expense not found.")
            
        success = update_expense(
            expense_id=expense_id,
            amount=expense.amount,
            category=expense.category,
            description=expense.description or "",
            date_str=expense.date
        )
        if success:
            return {"status": "success", "message": "Expense updated successfully."}
        else:
            raise HTTPException(status_code=500, detail="Failed to update expense.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/expenses/{expense_id}")
async def remove_expense(expense_id: int):
    """Delete an expense by ID."""
    try:
        exists = get_expense_by_id(expense_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Expense not found.")
            
        success = delete_expense(expense_id)
        if success:
            return {"status": "success", "message": "Expense deleted successfully."}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete expense.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/expenses/reset-mock")
async def reset_to_mock_data():
    """Reset the database and populate with mock data."""
    try:
        seed_mock_data()
        return {"status": "success", "message": "Database reset and seeded with mock expenses."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/expenses/summary")
async def get_summary():
    """Calculate and return dashboard statistics, category shares, and monthly totals."""
    try:
        expenses = get_all_expenses()
        if not expenses:
            return {
                "total": 0.0, "count": 0, "daily_avg": 0.0,
                "highest_category": "None", "breakdown": [], "trends": []
            }
            
        df = pd.DataFrame(expenses)
        df['amount'] = df['amount'].astype(float)
        df['date'] = pd.to_datetime(df['date'])
        
        # Core Metrics
        total = float(df['amount'].sum())
        count = int(df['id'].count())
        
        # Daily Average (based on days present in current data)
        unique_days = df['date'].nunique()
        daily_avg = float(total / unique_days) if unique_days > 0 else 0.0
        
        # Category Breakdown
        cat_group = df.groupby('category').agg(
            total_spent=('amount', 'sum'),
            count=('id', 'count')
        ).reset_index()
        cat_group['share_pct'] = (cat_group['total_spent'] / total * 100).round(2)
        cat_group = cat_group.sort_values(by='total_spent', ascending=False)
        
        highest_category = cat_group.iloc[0]['category'] if not cat_group.empty else "None"
        breakdown_list = cat_group.to_dict(orient='records')
        
        # Daily/Weekly trends
        trend_group = df.groupby('date').agg(amount=('amount', 'sum')).sort_index().reset_index()
        trend_group['date_str'] = trend_group['date'].dt.strftime('%Y-%m-%d')
        trends_list = trend_group[['date_str', 'amount']].to_dict(orient='records')
        
        return {
            "total": total,
            "count": count,
            "daily_avg": daily_avg,
            "highest_category": highest_category,
            "breakdown": breakdown_list,
            "trends": trends_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/expenses/export-excel")
async def export_excel():
    """Generate and return styled Excel spreadsheet for download."""
    try:
        expenses = get_all_expenses()
        output_dir = os.path.join(os.getcwd(), "output")
        output_filepath = os.path.join(output_dir, "expense_report.xlsx")
        
        export_expenses_to_excel(expenses, output_filepath)
        
        return FileResponse(
            path=output_filepath,
            filename=f"expense_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/expenses/upload-csv")
async def upload_expenses_csv(file: UploadFile = File(...)):
    """Bulk upload expenses via CSV file."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    try:
        contents = await file.read()
        decoded = contents.decode('utf-8', errors='ignore')
        df = pd.read_csv(io.StringIO(decoded))
        
        # Normalize column headers
        col_mapping = {}
        for col in df.columns:
            col_lower = str(col).strip().lower().replace("_", "").replace(" ", "")
            if col_lower in ['amount', 'spent', 'cost', 'price']:
                col_mapping[col] = 'amount'
            elif col_lower in ['category', 'type', 'cat']:
                col_mapping[col] = 'category'
            elif col_lower in ['description', 'desc', 'notes', 'title']:
                col_mapping[col] = 'description'
            elif col_lower in ['date', 'when', 'createdat', 'time']:
                col_mapping[col] = 'date'
                
        df.rename(columns=col_mapping, inplace=True)
        
        # Validate columns
        required = ['amount', 'category', 'date']
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns in CSV: {', '.join(missing)}")
            
        # Clean & parse columns
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
        df['category'] = df['category'].astype(str).str.strip().str.title()
        if 'description' not in df.columns:
            df['description'] = ""
        else:
            df['description'] = df['description'].fillna("").astype(str).str.strip()
            
        # Clean dates
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df.dropna(subset=['date'], inplace=True)
        df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # Bulk Insert
        expenses_to_add = df[['amount', 'category', 'description', 'date_str']].values.tolist()
        import sqlite3
        from src.database import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
            expenses_to_add
        )
        conn.commit()
        inserted_count = cursor.rowcount
        conn.close()
        
        return {"status": "success", "message": f"Successfully imported {inserted_count} expenses from CSV."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/expenses/download-sample-csv")
async def download_sample_csv():
    """Download template CSV for expense imports."""
    try:
        sample_data = {
            "Date": ["2026-06-01", "2026-06-02", "2026-06-03"],
            "Category": ["Food & Dining", "Transport", "Utilities"],
            "Amount": [15.50, 45.00, 120.00],
            "Description": ["Starbucks Coffee", "Weekly Gas refill", "Electricity bill"]
        }
        df = pd.DataFrame(sample_data)
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=expense_template.csv"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount Static UI Folder
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
