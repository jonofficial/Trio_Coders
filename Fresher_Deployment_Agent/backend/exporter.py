import pandas as pd
from datetime import datetime
from backend import settings
from backend.logger import logger
import os

def get_timestamped_filename(prefix: str) -> str:
    """Generates a filename with the current YYYYMMDD_HHMMSS timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.xlsx"

def export_pyramid_report(df: pd.DataFrame):
    """Exports the pyramid analysis report with required column groups."""
    filename = get_timestamped_filename(settings.PYRAMID_REPORT_PREFIX)
    file_path = settings.OUTPUT_DIR / filename
    logger.info(f"Exporting Pyramid Report to {file_path}")
    
    # Define Audit Date
    df['Audit Run Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Map internal flags to PDF required names
    df['Low Junior Warning'] = df.get('R1', False).map({True: 'YES', False: 'NO'})
    df['Over-Indexed Mid'] = df.get('R2', False).map({True: 'YES', False: 'NO'})
    df['Over-Indexed Senior'] = df.get('senior_gap', 0) < 0 # Simplified check
    df['Over-Indexed Senior'] = df['Over-Indexed Senior'].map({True: 'YES', False: 'NO'})
    df['Pyramid Health Status'] = df['flags'].apply(lambda x: 'Healthy' if 'Healthy' in x else 'Imbalance Detected')

    # PDF Schema Columns
    schema_map = {
        'project_id': 'Project ID',
        'project_name': 'Project Name / Account Name',
        'rm': 'RM',
        'total_headcount': 'Total Active Headcount',
        'junior_count': 'Junior Count',
        'mid_count': 'Mid Count',
        'senior_count': 'Senior Count',
        'junior_pct': 'Junior %',
        'mid_pct': 'Mid %',
        'senior_pct': 'Senior %',
        'junior_gap': 'Junior Gap (79 − Actual%)',
        'mid_gap': 'Mid Gap',
        'senior_gap': 'Senior Gap',
        'Low Junior Warning': 'Low Junior Warning',
        'Over-Indexed Mid': 'Over-Indexed Mid',
        'Over-Indexed Senior': 'Over-Indexed Senior',
        'Pyramid Health Status': 'Pyramid Health Status',
        'Audit Run Date': 'Audit Run Date'
    }
    
    export_df = df.rename(columns=schema_map)
    export_cols = [c for c in schema_map.values() if c in export_df.columns]
    
    try:
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            export_df[export_cols].to_excel(writer, sheet_name=settings.PYRAMID_SHEET_NAME, index=False)
        logger.info("Successfully exported Pyramid Report.")
    except Exception as e:
        logger.error(f"Failed to export Pyramid Report: {str(e)}")

def export_suggestions_report(df: pd.DataFrame, ris_data: pd.DataFrame):
    """Exports the deployment and training suggestions report."""
    filename = get_timestamped_filename(settings.SUGGESTIONS_REPORT_PREFIX)
    file_path = settings.OUTPUT_DIR / filename
    logger.info(f"Exporting Suggestions Report to {file_path}")
    
    # Add project metadata back (RM info)
    if 'rm' not in df.columns:
        project_meta = ris_data[['project_name', 'rm']].drop_duplicates(subset=['project_name'])
        df = pd.merge(df, project_meta, on='project_name', how='left')
    
    # Add pyramid metrics
    # Note: we should pass the aggregated data here or re-calculate. For simplicity, we assume columns exist or add Audit Date.
    df['Audit Run Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    schema_map = {
        'project_id': 'Project ID',
        'project_name': 'Project Name / Account Name',
        'rm': 'RM',
        'junior_pct': 'Junior %',
        'junior_gap': 'Junior Gap',
        'pyramid_health': 'Pyramid Health Status',
        'deployment_flag': 'Deployment Opportunity Flag',
        'suggested_fresher_count': 'Suggested Fresher Intake Count',
        'relevant_skills': 'Relevant Technologies',
        'primary_skills': 'Primary Skills Present',
        'training_track': 'Training Track Name',
        'training_curriculum': 'Curriculum Summary',
        'training_skills': 'Skills Covered',
        'training_flag': 'Training Suggestion Flag',
        'deployment_readiness_score': 'Deployment Readiness Score',
        'Audit Run Date': 'Audit Run Date'
    }
    
    export_df = df.rename(columns=schema_map)
    export_cols = [c for c in schema_map.values() if c in export_df.columns]
    
    try:
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            export_df[export_cols].to_excel(writer, sheet_name=settings.SUGGESTIONS_SHEET_NAME, index=False)
        logger.info("Successfully exported Suggestions Report.")
    except Exception as e:
        logger.error(f"Failed to export Suggestions Report: {str(e)}")
