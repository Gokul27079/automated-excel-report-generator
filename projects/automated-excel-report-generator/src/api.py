import os
import uuid
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

try:
    from src.ingest import load_csv_data
    from src.clean import clean_data
    from src.analyze import run_analysis
    from src.report import generate_report
    from src.mock_data import generate_mock_sales_data
except ImportError:
    from ingest import load_csv_data
    from clean import clean_data
    from analyze import run_analysis
    from report import generate_report
    from mock_data import generate_mock_sales_data

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_server")

app = FastAPI(
    title="Automated Excel Report Generator API",
    description="REST API for uploading sales CSV data, cleaning/analyzing it, and generating formatted Excel reports."
)

# CORS middleware to allow easy access if frontend is hosted separately
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to hold generated Excel files
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def process_dataframe(df_raw: pd.DataFrame) -> dict:
    """
    Helper function to execute the pipeline steps on a DataFrame and prepare UI JSON response.
    """
    raw_row_count = len(df_raw)
    
    # 1. Clean Data & track metrics
    # Row count after dropping nulls in Order ID or Revenue
    df_no_nulls = df_raw.dropna(subset=[col for col in df_raw.columns if str(col).lower().replace("_", "").replace(" ", "") in ['orderid', 'id', 'revenue', 'sales']])
    nulls_removed = raw_row_count - len(df_no_nulls)
    
    # Run the official clean module
    df_cleaned = clean_data(df_raw)
    clean_row_count = len(df_cleaned)
    duplicates_removed = len(df_no_nulls) - clean_row_count
    
    # 2. Run Analysis
    analysis = run_analysis(df_cleaned)
    
    # 3. Generate Report
    report_id = f"report_{uuid.uuid4().hex[:10]}"
    report_filename = f"{report_id}.xlsx"
    report_filepath = os.path.join(OUTPUT_DIR, report_filename)
    
    generate_report(df_raw, df_cleaned, analysis, report_filepath)
    
    # 4. Prepare JSON response
    # Convert dataframes to dictionaries for JSON serialization
    top_products_dict = analysis['top_products'].to_dict(orient='records')
    monthly_trends_dict = analysis['monthly_trends'].to_dict(orient='records')
    regional_sales_dict = analysis['regional_sales'].to_dict(orient='records')
    
    return {
        "status": "success",
        "report_id": report_id,
        "metrics": {
            "raw_rows": raw_row_count,
            "cleaned_rows": clean_row_count,
            "nulls_removed": max(0, nulls_removed),
            "duplicates_removed": max(0, duplicates_removed)
        },
        "kpis": analysis['kpis'],
        "top_products": top_products_dict,
        "monthly_trends": monthly_trends_dict,
        "regional_sales": regional_sales_dict
    }

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Endpoint to upload a raw CSV sales file, clean and analyze it, 
    generate an Excel report, and return dashboard statistics.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    try:
        contents = await file.read()
        df_raw = load_csv_data(contents)
        result = process_dataframe(df_raw)
        return result
    except Exception as e:
        logger.error(f"Error processing uploaded CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-from-mock")
async def generate_from_mock():
    """
    Endpoint to pre-populate and test the application with synthetic mock data.
    """
    try:
        # Generate messy mock sales data
        df_raw = generate_mock_sales_data(num_rows=250, messy=True)
        result = process_dataframe(df_raw)
        return result
    except Exception as e:
        logger.error(f"Error generating from mock data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{report_id}")
async def download_report(report_id: str):
    """
    Endpoint to download a generated Excel report.
    """
    report_filename = f"{report_id}.xlsx"
    report_filepath = os.path.join(OUTPUT_DIR, report_filename)
    
    if not os.path.exists(report_filepath):
        raise HTTPException(status_code=404, detail="Excel report not found or expired.")
        
    return FileResponse(
        path=report_filepath,
        filename=f"sales_report_{datetime_str()}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.get("/api/download-mock-csv")
async def download_mock_csv():
    """
    Endpoint to download a raw messy sales CSV file directly.
    """
    try:
        df_raw = generate_mock_sales_data(num_rows=200, messy=True)
        stream = io.StringIO()
        df_raw.to_csv(stream, index=False)
        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=mock_sales_data.csv"
        return response
    except Exception as e:
        logger.error(f"Error creating mock CSV download: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def datetime_str():
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# Mount Static Files (will serve index.html, style.css, app.js at the root '/')
# Check if static directory exists; if not, it will be created in next steps.
static_dir = os.path.join(os.getcwd(), "src", "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
