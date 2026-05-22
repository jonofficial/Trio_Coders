"""
agent.py — IAI Agent Orchestrator

Entry point that calls all modules in order:
  1. Load centralized configuration
  2. Initialize database schema
  3. Create run audit entry
  4. Data ingestion & preparation
  5. Rule engine evaluation
  6. Exception report generation (Excel)
  7. Database persistence (exceptions, rejected rows, config snapshot)
  8. RM team notification
  9. Update run audit with final status

Designed to be called from CLI or from FastAPI endpoint.
"""

import os
import sys
import logging
from datetime import datetime

# Add current directory to path to support local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_loader import Config
from data_preparation import DataPreparation
from rules_engine import RulesEngine
from schema import DatabaseManager
from notifier import Notifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class IAIAgent:
    """Orchestrates the full IAI pipeline."""

    def __init__(self, config: Config = None):
        """
        Initialize agent with a Config object.
        If none provided, creates a default Config from env/defaults.
        """
        self.config = config or Config()
        if not self.config._loaded:
            self.config.load()

        self.db_manager = DatabaseManager(db_url=self.config.database_url)
        self.notifier = Notifier(notification_url=self.config.rm_notification_url)

    def run(self, on_progress=None) -> dict:
        """
        Execute the full IAI pipeline. Returns a summary dict.

        Args:
            on_progress: Optional callback function(step_name: str, progress_pct: int)
        """
        run_timestamp = datetime.now().isoformat()
        result = {
            "run_id": -1,
            "status": "error",
            "run_timestamp": run_timestamp,
            "total_records": 0,
            "total_exceptions": 0,
            "exception_counts": {},
            "report_path": None,
            "error": None,
        }

        logger.info("=" * 70)
        logger.info("=== Starting Incorrect Allocation Identifier (IAI) Agent Workflow ===")
        logger.info("=" * 70)

        # The run_id will be generated during the atomic save at the end.
        run_id = -1

        try:
            # --- Step 1: Fetch Data ---
            if on_progress: on_progress("Fetch Data", 10)
            logger.info("--- Step 1: Fetch Data ---")
            dp = DataPreparation(
                ris_path=self.config.ris_path,
                so_path=self.config.so_path,
                contractor_codes=self.config.contractor_codes,
                support_sales_roles=self.config.support_sales_roles,
                psid_field=self.config.psid_field_name,
            )
            if on_progress: on_progress("Clean Data", 25)
            merged_df = dp.run()
            if on_progress: on_progress("Aggregate Allocation", 40)

            # Save merged snapshot
            merged_df.to_csv(self.config.merged_path, index=False)
            logger.info(f"Merged data snapshot saved to {self.config.merged_path}")

            result["total_records"] = dp.total_records_evaluated

            # --- Step 2: Validate Rules (R1–R7) ---
            if on_progress: on_progress("Validate Rules (R1–R7)", 55)
            logger.info("--- Step 2: Validate Rules (R1–R7) ---")
            engine = RulesEngine(
                merged_df=merged_df,
                contractor_codes=self.config.contractor_codes,
                support_sales_roles=self.config.support_sales_roles,
            )
            exceptions_df = engine.evaluate_rules()
            result["total_exceptions"] = len(exceptions_df)

            # Compute exception counts by rule
            if not exceptions_df.empty:
                exception_counts = exceptions_df['Rule ID'].value_counts().to_dict()
            else:
                exception_counts = {}
            result["exception_counts"] = exception_counts

            # --- Step 3: Generate Report ---
            if on_progress: on_progress("Generate Report", 75)
            logger.info("--- Step 3: Generate Report ---")
            report_path = engine.generate_report(exceptions_df, output_dir=self.config.output_dir)
            result["report_path"] = report_path

            # --- Step 4: Store Results ---
            if on_progress: on_progress("Store Results", 90)
            logger.info("--- Step 4: Store Results ---")
            status = "success" if not exceptions_df.empty else "no_exceptions"
            
            # Save everything atomically to ensure consistency
            run_id = self.db_manager.save_pipeline_results(
                ris_path=self.config.ris_path,
                so_path=self.config.so_path,
                total_records=dp.total_records_evaluated,
                total_exceptions=len(exceptions_df),
                exception_counts=exception_counts,
                status=status,
                error_message=None,
                exceptions_df=exceptions_df,
                rejected_df=dp.rejected_rows_df,
                config_dict=self.config.to_dict()
            )
            
            if run_id < 0:
                raise RuntimeError("Failed to save pipeline results to database.")
                
            result["run_id"] = run_id
            result["status"] = status

            # --- Step 7: RM Notification ---
            logger.info("--- Step 6: Notify Resource Management (RM) Team ---")
            self.notifier.notify(
                exception_count=len(exceptions_df),
                run_timestamp=run_timestamp,
                report_path=report_path,
                run_id=run_id,
            )

            logger.info("=" * 70)
            logger.info(f"=== Agent Workflow Completed: {len(exceptions_df)} exceptions found ===")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Critical error during pipeline execution: {e}", exc_info=True)
            result["status"] = "error"
            result["error"] = str(e)

            # Save failure to audit log
            failed_run_id = self.db_manager.create_run_audit(
                ris_file_path=self.config.ris_path,
                so_file_path=self.config.so_path,
            )
            self.db_manager.update_run_audit(
                run_id=failed_run_id,
                status="error",
                error_message=str(e),
            )
            result["run_id"] = failed_run_id

        return result


if __name__ == "__main__":
    agent = IAIAgent()
    result = agent.run()
    print(f"\n--- Run Summary ---")
    print(f"Run ID: {result['run_id']}")
    print(f"Status: {result['status']}")
    print(f"Records Evaluated: {result['total_records']}")
    print(f"Exceptions Found: {result['total_exceptions']}")
    print(f"Report: {result['report_path']}")
    if result['error']:
        print(f"Error: {result['error']}")