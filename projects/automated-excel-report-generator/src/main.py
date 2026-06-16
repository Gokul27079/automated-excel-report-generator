import os
import argparse
import logging
from datetime import datetime

# Import modules from src
try:
    from src.ingest import load_csv_data
    from src.clean import clean_data
    from src.analyze import run_analysis
    from src.report import generate_report
except ImportError:
    # Handle direct execution cases
    from ingest import load_csv_data
    from clean import clean_data
    from analyze import run_analysis
    from report import generate_report

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main_orchestrator")

def run_pipeline(input_csv: str, output_xlsx: str) -> str:
    """
    Runs the complete automated Excel report generation pipeline.
    """
    logger.info("Starting automated Excel report pipeline...")
    start_time = datetime.now()
    
    # 1. Ingest Data
    if not os.path.exists(input_csv):
        logger.warning(f"Input file not found at: {input_csv}. Generating mock data automatically...")
        input_dir = os.path.dirname(input_csv)
        if input_dir and not os.path.exists(input_dir):
            os.makedirs(input_dir)
        try:
            from mock_data import generate_mock_csv_string
        except ImportError:
            from src.mock_data import generate_mock_csv_string
            
        mock_csv = generate_mock_csv_string(num_rows=250, messy=True)
        with open(input_csv, "w", encoding="utf-8") as f:
            f.write(mock_csv)
        logger.info(f"Mock data successfully saved to: {input_csv}")
        
    logger.info(f"Ingesting raw data from: {input_csv}")
    raw_df = load_csv_data(input_csv)

    
    # 2. Clean Data
    logger.info("Cleaning raw sales data...")
    cleaned_df = clean_data(raw_df)
    
    # 3. Analyze Data
    logger.info("Running sales aggregates analysis...")
    analysis = run_analysis(cleaned_df)
    
    # 4. Generate Styled Excel Report with Embedded Charts
    logger.info(f"Generating formatted Excel report at: {output_xlsx}")
    generate_report(raw_df, cleaned_df, analysis, output_xlsx)
    
    duration = datetime.now() - start_time
    logger.info(f"Pipeline completed successfully in {duration.total_seconds():.2f} seconds!")
    return output_xlsx

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Excel Report Generator")
    parser.add_argument(
        "--input", 
        type=str, 
        default=os.path.join("data", "sales_data.csv"),
        help="Path to the raw sales CSV data file"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=os.path.join("output", "sales_report_June2026.xlsx"),
        help="Path where the final Excel file should be saved"
    )
    
    args = parser.parse_args()
    
    # Run pipeline
    try:
        run_pipeline(args.input, args.output)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        exit(1)
