import pandas as pd
import io
import logging

logger = logging.getLogger(__name__)

def load_csv_data(file_source) -> pd.DataFrame:
    """
    Loads raw CSV data from a file path, file-like object, or raw bytes.
    Returns a pandas DataFrame.
    """
    try:
        if isinstance(file_source, bytes):
            # Try to decode raw bytes
            decoded = file_source.decode('utf-8', errors='ignore')
            df = pd.read_csv(io.StringIO(decoded))
        elif isinstance(file_source, str):
            df = pd.read_csv(file_source)
        else:
            # Assume it's a file-like object
            df = pd.read_csv(file_source)
        
        logger.info(f"Successfully loaded CSV data with {len(df)} rows and {len(df.columns)} columns.")
        return df
    except Exception as e:
        logger.error(f"Failed to ingest CSV data: {str(e)}")
        raise ValueError(f"Failed to ingest CSV data: {str(e)}")
