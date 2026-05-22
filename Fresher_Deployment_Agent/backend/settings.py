import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent  # backend/
ROOT_DIR = BASE_DIR.parent                 # project root
CONFIG_DIR = BASE_DIR
OUTPUT_DIR = ROOT_DIR / "output"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Input Files
RIS_DATA_FILE = ROOT_DIR / "data" / "RIS_Synthetic.xlsx"
SO_DATA_FILE = ROOT_DIR / "data" / "SO_Ageing_Synthetic.xlsx"
GRADE_BAND_MAP_FILE = ROOT_DIR / "data" / "grade_band_map.csv"

# Pyramid Target Ratios (percentages)
TARGET_JUNIOR_PCT = 79.0
TARGET_MID_PCT = 20.0
TARGET_SENIOR_PCT = 1.0

# Rule Thresholds
# R2: High Fresher Intake
R2_HIGH_FRESHER_THRESHOLD_PCT = 85.0    # Junior% > this → high intake flag
R2_SMALL_TEAM_THRESHOLD = 10           # Team size <= this is considered "small"
R2_SMALL_TEAM_JUNIOR_RATIO = 0.667     # 2/3 of small team being junior triggers flag

# Column Mappings (Expected -> Actual in Synthetic Data)
RIS_COL_MAP = {
    'employee_id': 'Employee Email ID',
    'employee_name': 'Employee Name',
    'grade': 'Grade',
    'project_id': 'Project Id',
    'project_name': 'Project Name',
    'project_status': 'Project Status',
    'employee_status': 'Employee Status',
    'allocation_percent': '% Allocation',
    'start_date': 'Resource Start Date ',
    'end_date': 'Project end date',
    'project_role': 'Project Role',
    'technology': 'TalentX  - Core Skill',
    'skills': 'TalentX  Primary & Seconday Skills',
    'rm': 'RM'
}

SO_COL_MAP = {
    'project_id': 'Project ID',
    'project_name': 'Project Name',
    'skills': 'Primary Skill Description',
    'secondary_skills': 'Secondary Skill Description',
    'technology': 'Technology',
    'project_role': 'Project Role',
    'rm': 'Responsible for Staffing Name'
}

# Required columns for internal dataframes
RIS_REQUIRED_COLS = list(RIS_COL_MAP.keys())

# PDF Output Requirements
PYRAMID_REPORT_PREFIX = "FDA_PyramidReport"
PYRAMID_SHEET_NAME = "FDA_PyramidReport"

SUGGESTIONS_REPORT_PREFIX = "FDA_Suggestions"
SUGGESTIONS_SHEET_NAME = "FDA_Suggestions"
