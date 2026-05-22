"""
data_preparation.py — Data Ingestion, Cleaning, Merging & Aggregation

Handles the full data pipeline:
  1. Load RIS and SO Excel files
  2. Validate mandatory columns (halt on missing)
  3. Reject null-Emplid rows (logged separately)
  4. Clean/standardize data types
  5. Left-join RIS ← SO on Project Id
  6. Filter to active records
  7. Aggregate allocation per PSID
  8. Resolve bench signal per record (priority hierarchy)
"""

import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class DataPreparation:
    """Handles data ingestion, validation, cleaning, merging, and aggregation."""

    # Mandatory RIS columns — halt if any are missing
    MANDATORY_RIS_COLUMNS = [
        'Emplid', 'Employee Name', 'Task Type', 'Project Id', '% Allocation',
        'Resource End Date',
    ]

    # Optional RIS columns used by rules (we warn if missing but don't halt)
    OPTIONAL_RIS_COLUMNS = [
        'Project Name', 'Final Status', 'Total Allocation %', 'Allocation % Status',
        'Current or Future Bench', 'Bench Allocation Category', 'Project Type',
        'Project Category ', 'Location Category ', 'Onsite Status',
        'Supervisor Name', 'Supervisor Email ID', 'Employee Email ID',
        'Resource Based SL', 'Resource Based SSL', 'RM', 'Employee Status',
    ]

    def __init__(self, ris_path: str, so_path: str, contractor_codes: frozenset = None,
                 support_sales_roles: frozenset = None, psid_field: str = "Emplid"):
        self.ris_path = ris_path
        self.so_path = so_path
        self.contractor_codes = contractor_codes or frozenset()
        self.support_sales_roles = support_sales_roles or frozenset()
        self.psid_field = psid_field

        # Results populated after processing
        self.rejected_rows_df: pd.DataFrame = pd.DataFrame()
        self.total_records_evaluated: int = 0

    def run(self) -> pd.DataFrame:
        """Execute the full data preparation pipeline. Returns merged DataFrame."""
        logger.info("=== Data Preparation Pipeline Starting ===")

        # Step 1: Load raw data
        df_ris, df_so = self._load_raw_data()

        # Step 2: Validate mandatory columns
        self._validate_mandatory_columns(df_ris)

        # Step 3: Reject null-Emplid rows
        df_ris, self.rejected_rows_df = self._reject_null_emplid(df_ris)

        # Step 4: Clean and standardize
        df_ris = self._clean_ris(df_ris)
        df_so = self._clean_so(df_so)

        # Step 5: Left-join RIS ← SO
        merged_df = self._merge_data(df_ris, df_so)

        # Step 6: Aggregate allocation per PSID
        merged_df = self._aggregate_allocation(merged_df)

        # Step 7: Resolve bench signal per record
        merged_df = self._resolve_bench_signal(merged_df)

        self.total_records_evaluated = len(merged_df)
        logger.info(f"Data preparation complete. Final shape: {merged_df.shape}. "
                     f"Rejected rows: {len(self.rejected_rows_df)}")

        return merged_df

    # --- Legacy compatibility method ---
    def load_configs(self):
        """Legacy no-op. Configs are now loaded via Config object passed to constructor."""
        pass

    def load_and_clean_data(self) -> pd.DataFrame:
        """Legacy compatibility wrapper for agent.py."""
        return self.run()

    # --- Private Pipeline Steps ---

    def _load_raw_data(self) -> tuple:
        """Step 1: Load RIS and SO Excel files."""
        logger.info(f"Loading RIS data from {self.ris_path}")
        try:
            df_ris = pd.read_excel(self.ris_path)
            logger.info(f"RIS loaded: {df_ris.shape[0]} rows, {df_ris.shape[1]} columns")
        except Exception as e:
            logger.error(f"Failed to load RIS file: {e}")
            raise

        logger.info(f"Loading SO data from {self.so_path}")
        try:
            df_so = pd.read_excel(self.so_path)
            logger.info(f"SO loaded: {df_so.shape[0]} rows, {df_so.shape[1]} columns")
        except Exception as e:
            logger.error(f"Failed to load SO file: {e}")
            raise

        return df_ris, df_so

    def _validate_mandatory_columns(self, df_ris: pd.DataFrame):
        """Step 2: Check all mandatory columns exist. Halt on missing."""
        # Handle known column name mismatches in synthetic data
        if 'bench aging' in df_ris.columns and 'Emplid' not in df_ris.columns:
            df_ris.rename(columns={'bench aging': 'Emplid'}, inplace=True)
            logger.info("Renamed 'bench aging' column to 'Emplid' (synthetic data fix)")

        if 'Unnamed: 31' in df_ris.columns and 'Resource End Date' not in df_ris.columns:
            df_ris.rename(columns={'Unnamed: 31': 'Resource End Date'}, inplace=True)
            logger.info("Renamed 'Unnamed: 31' column to 'Resource End Date' (synthetic data fix)")

        missing_cols = [c for c in self.MANDATORY_RIS_COLUMNS if c not in df_ris.columns]
        if missing_cols:
            raise ValueError(f"Missing mandatory RIS columns: {missing_cols}. "
                             f"Available columns: {list(df_ris.columns)}")

        # Warn about missing optional columns
        missing_optional = [c for c in self.OPTIONAL_RIS_COLUMNS if c not in df_ris.columns]
        if missing_optional:
            logger.warning(f"Missing optional RIS columns (some rules may not fire): {missing_optional}")

    def _reject_null_emplid(self, df_ris: pd.DataFrame) -> tuple:
        """Step 3: Reject rows with null Emplid. Returns (clean_df, rejected_df)."""
        null_mask = df_ris[self.psid_field].isna()
        rejected = df_ris[null_mask].copy()
        clean = df_ris[~null_mask].copy()

        if len(rejected) > 0:
            logger.warning(f"Rejected {len(rejected)} rows due to null {self.psid_field}.")
            rejected['_rejection_reason'] = f"Null {self.psid_field}"
            rejected['_source_system'] = 'RIS'

        return clean, rejected

    def _clean_ris(self, df: pd.DataFrame) -> pd.DataFrame:
        """Step 4a: Clean and standardize RIS data."""
        # Emplid as string
        df[self.psid_field] = df[self.psid_field].astype(str).str.strip()

        # Task Type: uppercase stripped string
        task_col = 'Task Type'
        if task_col in df.columns:
            df[task_col] = df[task_col].astype(str).str.strip().str.upper()

        # Resource End Date: parse as datetime
        if 'Resource End Date' in df.columns:
            df['Resource End Date'] = pd.to_datetime(df['Resource End Date'], errors='coerce')
            # Add parseability flag for R6
            df['_end_date_parseable'] = df['Resource End Date'].notna()
            unparseable_count = (~df['_end_date_parseable']).sum()
            if unparseable_count > 0:
                logger.warning(f"Found {unparseable_count} unparseable 'Resource End Date' values. "
                               f"These will be excluded from R6 evaluation.")

        # % Allocation: numeric, clipped to [0, 100]
        alloc_col = '% Allocation'
        if alloc_col in df.columns:
            df[alloc_col] = pd.to_numeric(df[alloc_col], errors='coerce').fillna(0.0)
            out_of_range = df[(df[alloc_col] < 0) | (df[alloc_col] > 100)]
            if not out_of_range.empty:
                logger.warning(f"Found {len(out_of_range)} rows with % Allocation outside [0, 100]. Clipping.")
                df[alloc_col] = df[alloc_col].clip(0, 100)

        # Standardize Location Category (strip whitespace)
        for col in ['Location Category ', 'Location Category']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # Normalize Resource Based SSL — treat empty/whitespace as null
        for col in ['Resource Based SSL', 'Resource Based SSL ']:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: None if pd.isna(x) or str(x).strip() in ('', 'nan', 'NaN') else str(x).strip()
                )

        # Project Id as string
        if 'Project Id' in df.columns:
            df['Project Id'] = df['Project Id'].astype(str).str.strip()

        # Filter to active records
        if 'Final Status' in df.columns:
            inactive_statuses = ['inactive', 'closed']
            df = df[~df['Final Status'].astype(str).str.strip().str.lower().isin(inactive_statuses)]
            logger.info(f"Filtered active records based on Final Status. Remaining rows: {len(df)}")

        return df

    def _clean_so(self, df: pd.DataFrame) -> pd.DataFrame:
        """Step 4b: Clean and standardize SO data."""
        if 'Project ID' in df.columns:
            df['Project ID'] = df['Project ID'].astype(str).str.strip()
        return df

    def _merge_data(self, df_ris: pd.DataFrame, df_so: pd.DataFrame) -> pd.DataFrame:
        """Step 5: Left-join RIS ← SO on Project Id. Fill N/A for unmatched SO fields."""
        # Deduplicate SO by Project ID to prevent cartesian expansion
        if 'Project ID' in df_so.columns:
            df_so_unique = df_so.drop_duplicates(subset=['Project ID'])
        else:
            logger.warning("'Project ID' column not found in SO data. Skipping join.")
            return df_ris

        logger.info(f"Joining RIS ({len(df_ris)} rows) with SO ({len(df_so_unique)} unique projects)...")

        merged_df = pd.merge(
            df_ris,
            df_so_unique,
            left_on='Project Id',
            right_on='Project ID',
            how='left',
            suffixes=('_RIS', '_SO')
        )

        # Identify SO-sourced columns and fill N/A where no match
        so_columns = [c for c in df_so_unique.columns if c != 'Project ID']
        for col in so_columns:
            # After merge, SO columns may have _SO suffix
            target_col = f"{col}_SO" if f"{col}_SO" in merged_df.columns else col
            if target_col in merged_df.columns:
                merged_df[target_col] = merged_df[target_col].fillna('N/A')

        logger.info(f"Merge complete. Result shape: {merged_df.shape}")
        return merged_df

    def _aggregate_allocation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Step 6: Compute person-level total allocation."""
        # Find the correct allocation column (may have _RIS suffix after merge)
        alloc_col = '% Allocation_RIS' if '% Allocation_RIS' in df.columns else '% Allocation'

        if alloc_col not in df.columns:
            logger.warning(f"Allocation column '{alloc_col}' not found. Skipping aggregation.")
            return df

        person_alloc = df.groupby(self.psid_field)[alloc_col].sum().reset_index()
        person_alloc.rename(columns={alloc_col: 'Computed_Total_Allocation'}, inplace=True)

        df = df.merge(person_alloc, on=self.psid_field, how='left')
        logger.info(f"Allocation aggregation complete. "
                     f"Unique employees: {len(person_alloc)}")
        return df

    def _resolve_bench_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 7: Resolve bench signal per record using priority hierarchy:
          Priority 1: 'Current or Future Bench' field
          Priority 2: 'Bench Allocation Category' field
          Priority 3: 'Project Type' or 'Project Category ' field
        """
        def _is_bench_value(val):
            """Check if a field value indicates bench status."""
            if pd.isna(val) or str(val).strip() == '':
                return None  # No signal
            s = str(val).strip().lower()
            # Common truthy bench indicators
            bench_indicators = ['yes', 'y', 'true', '1', 'bench', 'current bench', 'future bench']
            return s in bench_indicators or 'bench' in s

        def resolve_bench(row):
            # Priority 1: Current or Future Bench
            for col in ['Current or Future Bench', 'Current or Future Bench ']:
                if col in row.index:
                    result = _is_bench_value(row[col])
                    if result is not None:
                        return result

            # Priority 2: Bench Allocation Category
            for col in ['Bench Allocation Category', 'Bench Allocation Category ']:
                if col in row.index:
                    result = _is_bench_value(row[col])
                    if result is not None:
                        return result

            # Priority 3: Project Type or Project Category
            for col in ['Project Type', 'Project Category ', 'Project Category']:
                if col in row.index:
                    val = row[col]
                    if pd.notna(val) and str(val).strip() != '':
                        s = str(val).strip().lower()
                        if 'bench' in s:
                            return True

            return False

        df['_bench_flag'] = df.apply(resolve_bench, axis=1)
        bench_count = df['_bench_flag'].sum()
        logger.info(f"Bench signal resolved. {bench_count} records flagged as on-bench.")
        return df


if __name__ == "__main__":
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "Data")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    dp = DataPreparation(
        ris_path=os.path.join(DATA_DIR, "RIS_Synthetic.xlsx"),
        so_path=os.path.join(DATA_DIR, "SO_Ageing_Synthetic.xlsx"),
    )
    merged = dp.run()
    # Save a merged preprocessed snapshot for agent usage
    output_path = os.path.join(DATA_DIR, "Merged_Prepared_Data.csv")
    merged.to_csv(output_path, index=False)
    logger.info(f"Snapshot written to {output_path}")
