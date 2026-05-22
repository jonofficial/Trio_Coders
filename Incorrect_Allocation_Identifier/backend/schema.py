"""
schema.py — PostgreSQL Persistence Layer

Manages all database operations:
  - Schema creation (4 tables: iai_run_audit, iai_exceptions, iai_rejected_rows, iai_config_snapshot)
  - Run audit logging
  - Exception persistence
  - Rejected row logging
  - Config snapshot storage
  - Query methods for API layer

Connection string loaded from .env (never hardcoded).
"""

import pandas as pd
import logging
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL schema creation, audit logging, and data persistence."""

    def __init__(self, db_url: str = None):
        self.db_url = db_url
        self.engine = None

        if self.db_url:
            try:
                self.engine = create_engine(self.db_url, pool_pre_ping=True)
                logger.info("SQLAlchemy engine initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize SQLAlchemy engine: {e}")
                self.engine = None
        else:
            logger.warning("No DATABASE_URL provided. Database operations will be skipped.")

    # ==================== Schema Initialization ====================

    def initialize_schema(self):
        """Creates all required tables if they do not exist."""
        if not self.engine:
            logger.warning("No database engine available. Skipping schema initialization.")
            return False

        schema_sql = """
        -- Run audit log
        CREATE TABLE IF NOT EXISTS iai_run_audit (
            run_id SERIAL PRIMARY KEY,
            run_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            ris_file_path TEXT,
            so_file_path TEXT,
            total_records_evaluated INTEGER,
            total_exceptions INTEGER,
            exception_count_by_rule JSONB,
            run_status TEXT,
            error_message TEXT
        );

        -- Exception records staging
        CREATE TABLE IF NOT EXISTS iai_exceptions (
            exception_id SERIAL PRIMARY KEY,
            run_id INTEGER REFERENCES iai_run_audit(run_id),
            psid TEXT NOT NULL,
            employee_name TEXT,
            rule_id TEXT NOT NULL,
            rule_name TEXT,
            exception_reason TEXT,
            severity TEXT,
            task_type TEXT,
            project_id TEXT,
            project_name TEXT,
            so_id TEXT,
            project_role TEXT,
            project_type TEXT,
            total_allocation_pct NUMERIC,
            row_allocation_pct NUMERIC,
            allocation_status TEXT,
            location_category TEXT,
            onsite_status TEXT,
            bench_flag BOOLEAN,
            resource_end_date DATE,
            days_past_end_date INTEGER,
            resource_based_sl TEXT,
            resource_based_ssl TEXT,
            so_resource_base_ssl TEXT,
            mode_of_hire TEXT,
            employee_status TEXT,
            grade TEXT,
            rm TEXT,
            supervisor_name TEXT,
            supervisor_email TEXT,
            recommended_action TEXT,
            run_date TIMESTAMPTZ
        );

        -- Rejected rows log
        CREATE TABLE IF NOT EXISTS iai_rejected_rows (
            rejection_id SERIAL PRIMARY KEY,
            run_id INTEGER REFERENCES iai_run_audit(run_id),
            source_system TEXT,
            row_index INTEGER,
            rejection_reason TEXT,
            raw_data JSONB
        );

        -- Config snapshot (for reproducibility)
        CREATE TABLE IF NOT EXISTS iai_config_snapshot (
            snapshot_id SERIAL PRIMARY KEY,
            run_id INTEGER REFERENCES iai_run_audit(run_id),
            contractor_codes JSONB,
            support_sales_roles JSONB,
            psid_field_name TEXT
        );
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(text(schema_sql))
            logger.info("Database schema initialized successfully (4 tables verified).")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error initializing schema: {e}")
            return False

    # ==================== Run Audit ====================

    def create_run_audit(self, ris_file_path: str = None, so_file_path: str = None) -> int:
        """Create a new run audit entry. Returns the run_id."""
        if not self.engine:
            logger.warning("No database engine. Skipping run audit creation.")
            return -1

        try:
            with self.engine.begin() as conn:
                result = conn.execute(
                    text("""
                        INSERT INTO iai_run_audit (run_timestamp, ris_file_path, so_file_path, run_status)
                        VALUES (NOW(), :ris_path, :so_path, 'running')
                        RETURNING run_id
                    """),
                    {"ris_path": ris_file_path, "so_path": so_file_path}
                )
                run_id = result.fetchone()[0]
                logger.info(f"Run audit created: run_id={run_id}")
                return run_id
        except SQLAlchemyError as e:
            logger.error(f"Error creating run audit: {e}")
            return -1

    def update_run_audit(self, run_id: int, total_records: int = 0,
                         total_exceptions: int = 0, exception_counts: dict = None,
                         status: str = "success", error_message: str = None):
        """Update the run audit with final results."""
        if not self.engine or run_id < 0:
            return

        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE iai_run_audit
                        SET total_records_evaluated = :total_records,
                            total_exceptions = :total_exceptions,
                            exception_count_by_rule = :counts,
                            run_status = :status,
                            error_message = :error_msg
                        WHERE run_id = :run_id
                    """),
                    {
                        "run_id": run_id,
                        "total_records": total_records,
                        "total_exceptions": total_exceptions,
                        "counts": json.dumps(exception_counts or {}),
                        "status": status,
                        "error_msg": error_message,
                    }
                )
                logger.info(f"Run audit updated: run_id={run_id}, status={status}")
        except SQLAlchemyError as e:
            logger.error(f"Error updating run audit: {e}")

    # ==================== Exception Persistence ====================

    def save_exceptions(self, exceptions_df: pd.DataFrame, run_id: int = -1):
        """Save the exceptions report to the database."""
        if not self.engine:
            logger.warning("No database engine. Skipping exception save.")
            return

        if exceptions_df.empty:
            logger.info("Empty exceptions DataFrame. Nothing to save.")
            return

        try:
            db_df = pd.DataFrame()
            # Assign data column FIRST to establish DataFrame length
            db_df['psid'] = exceptions_df['Emplid'].astype(str).values
            db_df['run_id'] = run_id if run_id >= 0 else None  # Now broadcasts correctly
            db_df['employee_name'] = exceptions_df.get('Employee Name', 'N/A').values
            db_df['rule_id'] = exceptions_df['Rule ID'].values
            db_df['rule_name'] = exceptions_df['Rule Name'].values
            db_df['exception_reason'] = exceptions_df['Exception Description'].values
            db_df['severity'] = exceptions_df['Severity'].values
            db_df['task_type'] = exceptions_df.get('Task Type', 'N/A')
            db_df['project_id'] = exceptions_df.get('Project Id', 'N/A').astype(str)
            db_df['project_name'] = exceptions_df.get('Project Name', 'N/A')
            db_df['so_id'] = exceptions_df.get('SO ID', 'N/A')
            db_df['project_role'] = exceptions_df.get('Project Role', 'N/A')
            db_df['project_type'] = exceptions_df.get('Project Type', 'N/A')

            # Numeric columns — handle N/A values
            db_df['total_allocation_pct'] = pd.to_numeric(
                exceptions_df.get('Computed_Total_Allocation', pd.Series(dtype=float)),
                errors='coerce'
            )
            db_df['row_allocation_pct'] = pd.to_numeric(
                exceptions_df.get('% Allocation', pd.Series(dtype=float)),
                errors='coerce'
            )
            db_df['allocation_status'] = exceptions_df.get('Allocation % Status', 'N/A')
            db_df['location_category'] = exceptions_df.get('Location Category', 'N/A')
            db_df['onsite_status'] = exceptions_df.get('Onsite Status', 'N/A')

            # Bench flag
            bench = exceptions_df.get('Bench Flag', pd.Series(dtype=str))
            db_df['bench_flag'] = bench.map(
                lambda x: True if str(x).strip().lower() in ('true', '1', 'yes') else
                (False if str(x).strip().lower() in ('false', '0', 'no') else None)
            )

            db_df['resource_end_date'] = pd.to_datetime(
                exceptions_df.get('Resource End Date', pd.Series(dtype=str)),
                errors='coerce'
            )
            db_df['days_past_end_date'] = pd.to_numeric(
                exceptions_df.get('Days Past End Date', pd.Series(dtype=float)),
                errors='coerce'
            ).astype('Int64')  # nullable int

            db_df['resource_based_sl'] = exceptions_df.get('Resource Based SL', 'N/A')
            db_df['resource_based_ssl'] = exceptions_df.get('Resource Based SSL', 'N/A')
            db_df['so_resource_base_ssl'] = exceptions_df.get('SO Resource Base SSL', 'N/A')
            db_df['mode_of_hire'] = exceptions_df.get('Mode of Hire', 'N/A')
            db_df['employee_status'] = exceptions_df.get('Employee Status', 'N/A')
            db_df['grade'] = exceptions_df.get('Grade', 'N/A')
            db_df['rm'] = exceptions_df.get('RM', 'N/A')
            db_df['supervisor_name'] = exceptions_df.get('Supervisor Name', 'N/A')
            db_df['supervisor_email'] = exceptions_df.get('Supervisor Email', 'N/A')
            db_df['recommended_action'] = exceptions_df.get('Recommended Action', 'N/A')
            db_df['run_date'] = pd.Timestamp.now()

            db_df.to_sql('iai_exceptions', self.engine, if_exists='append', index=False)
            logger.info(f"Saved {len(db_df)} exceptions to database (run_id={run_id}).")
        except SQLAlchemyError as e:
            logger.error(f"Error saving exceptions to database: {e}")
        except Exception as e:
            logger.error(f"Error mapping exception data for DB save: {e}")

    # ==================== Rejected Rows ====================

    def save_rejected_rows(self, rejected_df: pd.DataFrame, run_id: int = -1):
        """Save rejected rows (null Emplid etc.) to the database."""
        if not self.engine or rejected_df.empty:
            return

        try:
            rows_to_insert = []
            for idx, row in rejected_df.iterrows():
                rows_to_insert.append({
                    "run_id": run_id if run_id >= 0 else None,
                    "source_system": row.get('_source_system', 'RIS'),
                    "row_index": int(idx),
                    "rejection_reason": row.get('_rejection_reason', 'Unknown'),
                    "raw_data": json.dumps(
                        {k: str(v) for k, v in row.items() if not k.startswith('_')},
                        default=str
                    ),
                })

            with self.engine.begin() as conn:
                for r in rows_to_insert:
                    conn.execute(
                        text("""
                            INSERT INTO iai_rejected_rows (run_id, source_system, row_index, rejection_reason, raw_data)
                            VALUES (:run_id, :source_system, :row_index, :rejection_reason, :raw_data::jsonb)
                        """),
                        r
                    )
            logger.info(f"Saved {len(rows_to_insert)} rejected rows to database.")
        except SQLAlchemyError as e:
            logger.error(f"Error saving rejected rows: {e}")

    # ==================== Config Snapshot ====================

    def save_config_snapshot(self, run_id: int, config_dict: dict):
        """Save a snapshot of the configuration used for this run."""
        if not self.engine or run_id < 0:
            return

        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO iai_config_snapshot (run_id, contractor_codes, support_sales_roles, psid_field_name)
                        VALUES (:run_id, :contractor_codes, :support_sales_roles, :psid_field_name)
                    """),
                    {
                        "run_id": run_id,
                        "contractor_codes": json.dumps(config_dict.get("contractor_codes", [])),
                        "support_sales_roles": json.dumps(config_dict.get("support_sales_roles", [])),
                        "psid_field_name": config_dict.get("psid_field_name", "Emplid"),
                    }
                )
            logger.info(f"Config snapshot saved for run_id={run_id}.")
        except SQLAlchemyError as e:
            logger.error(f"Error saving config snapshot: {e}")

    # ==================== Atomic Pipeline Save ====================

    def save_pipeline_results(self, ris_path: str, so_path: str, total_records: int,
                              total_exceptions: int, exception_counts: dict,
                              status: str, error_message: str,
                              exceptions_df: pd.DataFrame, rejected_df: pd.DataFrame,
                              config_dict: dict) -> int:
        """Atomically save the entire pipeline run to ensure consistency and prevent partial writes."""
        if not self.engine:
            logger.warning("No database engine. Skipping atomic save.")
            return -1

        try:
            with self.engine.begin() as conn:
                # 1. Insert Run Audit
                result = conn.execute(
                    text("""
                        INSERT INTO iai_run_audit (
                            run_timestamp, ris_file_path, so_file_path, 
                            total_records_evaluated, total_exceptions, 
                            exception_count_by_rule, run_status, error_message
                        )
                        VALUES (NOW(), :ris_path, :so_path, :total_records, :total_exceptions, :counts, :status, :error_msg)
                        RETURNING run_id
                    """),
                    {
                        "ris_path": ris_path, "so_path": so_path,
                        "total_records": total_records, "total_exceptions": total_exceptions,
                        "counts": json.dumps(exception_counts or {}),
                        "status": status, "error_msg": error_message,
                    }
                )
                run_id = result.fetchone()[0]

                # 2. Insert Config Snapshot
                conn.execute(
                    text("""
                        INSERT INTO iai_config_snapshot (run_id, contractor_codes, support_sales_roles, psid_field_name)
                        VALUES (:run_id, :contractor_codes, :support_sales_roles, :psid_field_name)
                    """),
                    {
                        "run_id": run_id,
                        "contractor_codes": json.dumps(config_dict.get("contractor_codes", [])),
                        "support_sales_roles": json.dumps(config_dict.get("support_sales_roles", [])),
                        "psid_field_name": config_dict.get("psid_field_name", "Emplid"),
                    }
                )

                # 3. Insert Exceptions
                if not exceptions_df.empty:
                    db_df = pd.DataFrame()
                    # IMPORTANT: Assign data columns FIRST to establish DataFrame length,
                    # then set run_id as a constant — scalar broadcasts to all rows.
                    db_df['psid'] = exceptions_df['Emplid'].astype(str).values
                    db_df['run_id'] = run_id  # Now broadcasts to len(db_df) rows
                    db_df['employee_name'] = exceptions_df.get('Employee Name', 'N/A').values
                    db_df['rule_id'] = exceptions_df['Rule ID'].values
                    db_df['rule_name'] = exceptions_df['Rule Name'].values
                    db_df['exception_reason'] = exceptions_df['Exception Description'].values
                    db_df['severity'] = exceptions_df['Severity'].values
                    db_df['task_type'] = exceptions_df.get('Task Type', 'N/A').values
                    db_df['project_id'] = exceptions_df.get('Project Id', 'N/A').astype(str).values
                    db_df['project_name'] = exceptions_df.get('Project Name', 'N/A').values
                    db_df['so_id'] = exceptions_df.get('SO ID', 'N/A').values
                    db_df['project_role'] = exceptions_df.get('Project Role', 'N/A').values
                    db_df['project_type'] = exceptions_df.get('Project Type', 'N/A').values

                    db_df['total_allocation_pct'] = pd.to_numeric(exceptions_df.get('Computed_Total_Allocation', pd.Series(dtype=float)), errors='coerce').values
                    db_df['row_allocation_pct'] = pd.to_numeric(exceptions_df.get('% Allocation', pd.Series(dtype=float)), errors='coerce').values
                    db_df['allocation_status'] = exceptions_df.get('Allocation % Status', 'N/A').values
                    db_df['location_category'] = exceptions_df.get('Location Category', 'N/A').values
                    db_df['onsite_status'] = exceptions_df.get('Onsite Status', 'N/A').values

                    bench = exceptions_df.get('Bench Flag', pd.Series(dtype=str))
                    db_df['bench_flag'] = bench.map(lambda x: True if str(x).strip().lower() in ('true', '1', 'yes') else (False if str(x).strip().lower() in ('false', '0', 'no') else None)).values
                    db_df['resource_end_date'] = pd.to_datetime(exceptions_df.get('Resource End Date', pd.Series(dtype=str)), errors='coerce').values
                    db_df['days_past_end_date'] = pd.to_numeric(exceptions_df.get('Days Past End Date', pd.Series(dtype=float)), errors='coerce').astype('Int64').values
                    db_df['resource_based_sl'] = exceptions_df.get('Resource Based SL', 'N/A').values
                    db_df['resource_based_ssl'] = exceptions_df.get('Resource Based SSL', 'N/A').values
                    db_df['so_resource_base_ssl'] = exceptions_df.get('SO Resource Base SSL', 'N/A').values
                    db_df['mode_of_hire'] = exceptions_df.get('Mode of Hire', 'N/A').values
                    db_df['employee_status'] = exceptions_df.get('Employee Status', 'N/A').values
                    db_df['grade'] = exceptions_df.get('Grade', 'N/A').values
                    db_df['rm'] = exceptions_df.get('RM', 'N/A').values
                    db_df['supervisor_name'] = exceptions_df.get('Supervisor Name', 'N/A').values
                    db_df['supervisor_email'] = exceptions_df.get('Supervisor Email', 'N/A').values
                    db_df['recommended_action'] = exceptions_df.get('Recommended Action', 'N/A').values
                    db_df['run_date'] = pd.Timestamp.now()

                    db_df.to_sql('iai_exceptions', conn, if_exists='append', index=False)

                # 4. Insert Rejected Rows
                if not rejected_df.empty:
                    rows_to_insert = []
                    for idx, row in rejected_df.iterrows():
                        rows_to_insert.append({
                            "run_id": run_id,
                            "source_system": row.get('_source_system', 'RIS'),
                            "row_index": int(idx),
                            "rejection_reason": row.get('_rejection_reason', 'Unknown'),
                            "raw_data": json.dumps({k: str(v) for k, v in row.items() if not k.startswith('_')}, default=str),
                        })
                    for r in rows_to_insert:
                        conn.execute(
                            text("""
                                INSERT INTO iai_rejected_rows (run_id, source_system, row_index, rejection_reason, raw_data)
                                VALUES (:run_id, :source_system, :row_index, :rejection_reason, :raw_data::jsonb)
                            """),
                            r
                        )

                logger.info(f"Atomically saved full pipeline results for run_id={run_id}.")
                return run_id

        except SQLAlchemyError as e:
            logger.error(f"Error during atomic pipeline save: {e}")
            return -1

    # ==================== Query Methods (for API) ====================

    def get_runs(self, limit: int = 50) -> list:
        """Fetch recent run audit records."""
        if not self.engine:
            return []
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM iai_run_audit ORDER BY run_id DESC LIMIT :limit"),
                    {"limit": limit}
                )
                rows = result.mappings().all()
                return [dict(r) for r in rows]
        except SQLAlchemyError as e:
            logger.error(f"Error fetching runs: {e}")
            return []

    def _get_exception_filters(self, run_id: int = None, psid: str = None) -> tuple[str, dict]:
        """Returns the consistent WHERE clause and parameters for querying exceptions."""
        params = {}
        if run_id is not None:
            where_clause = "WHERE run_id = :run_id"
            params["run_id"] = run_id
        else:
            where_clause = """
                WHERE run_id = (SELECT MAX(run_id) FROM iai_run_audit WHERE run_status IN ('success', 'no_exceptions'))
            """
            
        if psid is not None:
            where_clause += " AND psid = :psid"
            params["psid"] = psid
            
        return where_clause, params

    def get_exceptions(self, run_id: int = None, limit: int = 500, psid: str = None) -> list:
        """Fetch exception records, optionally filtered by run_id or psid."""
        if not self.engine:
            return []
        try:
            with self.engine.connect() as conn:
                if run_id is not None:
                    # Repair orphaned exceptions with null run_id (historical bug fix)
                    conn.execute(
                        text("""
                            UPDATE iai_exceptions SET run_id = :run_id
                            WHERE run_id IS NULL
                            AND run_date >= (
                                SELECT run_timestamp - INTERVAL '24 hours'
                                FROM iai_run_audit WHERE run_id = :run_id
                            )
                            AND run_date <= (
                                SELECT run_timestamp + INTERVAL '24 hours'
                                FROM iai_run_audit WHERE run_id = :run_id
                            )
                        """),
                        {"run_id": run_id}
                    )
                    conn.commit()

                where_clause, params = self._get_exception_filters(run_id, psid)
                params["limit"] = limit
                
                query = f"SELECT * FROM iai_exceptions {where_clause} ORDER BY exception_id DESC LIMIT :limit"
                logger.debug(f"Executing get_exceptions with query: {query} | params: {params}")
                
                result = conn.execute(text(query), params)
                rows = result.mappings().all()
                return [dict(r) for r in rows]
        except SQLAlchemyError as e:
            logger.error(f"Error fetching exceptions: {e}")
            return []

    def get_top_violators(self, run_id: int = None, limit: int = 10) -> list:
        """Aggregate violations by employee (PSID) using identical filters to get_exceptions."""
        if not self.engine: return []
        try:
            with self.engine.connect() as conn:
                where_clause, params = self._get_exception_filters(run_id)
                params["limit"] = limit
                
                query = f"""
                    SELECT psid, employee_name, COUNT(*) as violation_count
                    FROM iai_exceptions
                    {where_clause}
                    GROUP BY psid, employee_name
                    ORDER BY violation_count DESC
                    LIMIT :limit
                """
                logger.debug(f"Executing get_top_violators with query: {query} | params: {params}")
                
                result = conn.execute(text(query), params)
                rows = result.mappings().all()
                return [dict(r) for r in rows]
        except SQLAlchemyError as e:
            logger.error(f"Error fetching top violators: {e}")
            return []

    def get_summary(self, run_id: int) -> dict:
        """Get summary statistics for a specific run."""
        if not self.engine:
            return {}
        try:
            with self.engine.connect() as conn:
                # First, repair any orphaned exceptions with null run_id
                # This fixes the historical bug where run_id wasn't persisted
                # Use 24h window to handle UTC vs local timezone differences
                conn.execute(
                    text("""
                        UPDATE iai_exceptions SET run_id = :run_id
                        WHERE run_id IS NULL
                        AND run_date >= (
                            SELECT run_timestamp - INTERVAL '24 hours'
                            FROM iai_run_audit WHERE run_id = :run_id
                        )
                        AND run_date <= (
                            SELECT run_timestamp + INTERVAL '24 hours'
                            FROM iai_run_audit WHERE run_id = :run_id
                        )
                    """),
                    {"run_id": run_id}
                )
                conn.commit()

                # Counts by rule
                rule_counts = conn.execute(
                    text("""
                        SELECT rule_id, rule_name, severity, COUNT(*) as count
                        FROM iai_exceptions WHERE run_id = :run_id
                        GROUP BY rule_id, rule_name, severity
                        ORDER BY rule_id
                    """),
                    {"run_id": run_id}
                ).mappings().all()

                # Counts by severity
                severity_counts = conn.execute(
                    text("""
                        SELECT severity, COUNT(*) as count
                        FROM iai_exceptions WHERE run_id = :run_id
                        GROUP BY severity
                    """),
                    {"run_id": run_id}
                ).mappings().all()

                # Run metadata
                run_info = conn.execute(
                    text("SELECT * FROM iai_run_audit WHERE run_id = :run_id"),
                    {"run_id": run_id}
                ).mappings().fetchone()

                by_rule = [dict(r) for r in rule_counts]
                by_severity = [dict(r) for r in severity_counts]

                # Fallback: if exception table queries returned empty,
                # derive from exception_count_by_rule stored in run_audit
                if not by_rule and run_info:
                    ecbr = run_info.get("exception_count_by_rule")
                    if ecbr:
                        import json as json_mod
                        counts = ecbr if isinstance(ecbr, dict) else json_mod.loads(ecbr)
                        # We don't have severity info in the fallback, 
                        # so use our rules reference
                        RULE_SEVERITY = {
                            "R1": ("Unassigned Task", "High"),
                            "R2": ("Incorrect Task Tag", "Medium"),
                            "R3": ("Allocation ≠ 100%", "Critical"),
                            "R4": ("Contractor on Bench", "High"),
                            "R5": ("Onsite on Bench", "High"),
                            "R6": ("Stale Long Leave", "Medium"),
                            "R7": ("Missing RSSL", "Medium"),
                        }
                        for rule_id, count in counts.items():
                            name, sev = RULE_SEVERITY.get(rule_id, (rule_id, "Medium"))
                            by_rule.append({"rule_id": rule_id, "rule_name": name, "severity": sev, "count": count})
                        
                        # Derive by_severity from the fallback
                        sev_map = {}
                        for item in by_rule:
                            s = item["severity"]
                            sev_map[s] = sev_map.get(s, 0) + item["count"]
                        by_severity = [{"severity": s, "count": c} for s, c in sev_map.items()]

                return {
                    "run_id": run_id,
                    "run_info": dict(run_info) if run_info else None,
                    "by_rule": by_rule,
                    "by_severity": by_severity,
                }
        except SQLAlchemyError as e:
            logger.error(f"Error fetching summary: {e}")
            return {}

    def is_connected(self) -> bool:
        """Check if the database connection is alive."""
        if not self.engine:
            return False
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
