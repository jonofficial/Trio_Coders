import pandas as pd
from backend import settings
from backend.logger import logger

def map_columns(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    """Maps columns from synthetic data names to internal system names via exact + fuzzy match."""
    available_cols = df.columns.tolist()
    rename_dict = {}
    
    for internal_name, actual_name in col_map.items():
        if actual_name in available_cols:
            rename_dict[actual_name] = internal_name
        else:
            # Fuzzy match: strip whitespace and case-insensitive compare
            clean_actual = actual_name.strip().lower()
            found = False
            for col in available_cols:
                if col.strip().lower() == clean_actual:
                    rename_dict[col] = internal_name
                    found = True
                    break
            if not found:
                logger.warning(f"Column '{actual_name}' (→'{internal_name}') not found in dataframe.")
    
    return df.rename(columns=rename_dict)

def load_ris_data(file_path: str = settings.RIS_DATA_FILE) -> pd.DataFrame:
    """Loads RIS data from the Excel file and applies internal column mapping."""
    logger.info(f"Loading RIS data from {file_path}")
    try:
        df = pd.read_excel(file_path, dtype=str)
        logger.info(f"Successfully loaded {len(df)} records from RIS data.")
        df = map_columns(df, settings.RIS_COL_MAP)
        
        # Coerce allocation to numeric
        if 'allocation_percent' in df.columns:
            df['allocation_percent'] = pd.to_numeric(df['allocation_percent'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        logger.error(f"Failed to load RIS data: {str(e)}")
        raise

def load_so_data(file_path: str = settings.SO_DATA_FILE) -> pd.DataFrame:
    """Loads SO Ageing data from the Excel file and applies internal column mapping."""
    logger.info(f"Loading SO data from {file_path}")
    try:
        df = pd.read_excel(file_path, dtype=str)
        logger.info(f"Successfully loaded {len(df)} records from SO data.")
        df = map_columns(df, settings.SO_COL_MAP)
        return df
    except Exception as e:
        logger.error(f"Failed to load SO data: {str(e)}")
        raise
