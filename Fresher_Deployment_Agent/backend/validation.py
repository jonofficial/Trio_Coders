import pandas as pd
from backend import settings
from backend.logger import logger

def load_grade_band_map(file_path: str = settings.GRADE_BAND_MAP_FILE) -> dict:
    """Loads the grade to band mapping from CSV."""
    try:
        df = pd.read_csv(file_path)
        return dict(zip(df['grade'], df['band']))
    except Exception as e:
        logger.error(f"Failed to load grade band map from {file_path}: {str(e)}")
        raise

def filter_active_resources(df: pd.DataFrame) -> pd.DataFrame:
    """Filters the RIS dataframe to only include active resources."""
    initial_count = len(df)
    
    # Filter based on allocation (default to True if column missing)
    if 'allocation_percent' in df.columns:
        alloc_mask = df['allocation_percent'] > 0
    else:
        alloc_mask = pd.Series([True] * len(df))
        
    # Filter based on employee status
    if 'employee_status' in df.columns:
        emp_status_mask = ~df['employee_status'].str.lower().isin(['resigned', 'exit', 'terminated'])
    else:
        emp_status_mask = pd.Series([True] * len(df))
        
    # Filter based on project status
    if 'project_status' in df.columns:
        proj_status_mask = ~df['project_status'].str.lower().isin(['closed', 'completed'])
    else:
        proj_status_mask = pd.Series([True] * len(df))
        
    active_df = df[alloc_mask & emp_status_mask & proj_status_mask].copy()
    
    filtered_count = len(active_df)
    logger.info(f"Filtered active resources: {filtered_count} / {initial_count} records kept.")
    
    return active_df

def map_grades_to_bands(df: pd.DataFrame, grade_map: dict) -> pd.DataFrame:
    """Maps the 'grade' column to 'band' and filters out unmapped records."""
    if 'grade' not in df.columns:
        logger.error("'grade' column missing from dataframe.")
        return df
        
    df['band'] = df['grade'].map(grade_map)
    
    unmapped_mask = df['band'].isna()
    if unmapped_mask.any():
        unmapped_grades = df.loc[unmapped_mask, 'grade'].unique()
        logger.warning(f"Unmapped grades found: {unmapped_grades}. Excluding {unmapped_mask.sum()} records.")
            
    mapped_df = df.dropna(subset=['band']).copy()
    return mapped_df

def prepare_clean_ris_data(df: pd.DataFrame) -> pd.DataFrame:
    """Executes the full cleaning and validation pipeline on RIS data."""
    logger.info("Starting RIS data validation and cleaning.")
    
    # 1. Filter active
    active_df = filter_active_resources(df)
    
    # 2. Load and Map grades
    grade_map = load_grade_band_map()
    clean_df = map_grades_to_bands(active_df, grade_map)
    
    # 3. Ensure required columns are present
    for col in settings.RIS_REQUIRED_COLS:
        if col not in clean_df.columns:
            clean_df[col] = "N/A"
            
    logger.info("RIS data preparation complete.")
    return clean_df
