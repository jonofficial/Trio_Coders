"""
main.py — FastAPI Entry Point for the IAI Agent

Provides REST API endpoints to:
  - Check system health
  - Trigger the full IAI pipeline
  - Fetch stored exception results
  - Fetch run history
  - Fetch summary statistics

Business logic stays in backend/ — this is a thin API layer.
"""

import logging
import threading
import uuid
from datetime import datetime
from typing import Optional, List
import sys
import os

# Add current directory to path to support local imports when moved
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import csv

from pydantic import BaseModel, Field

from config_loader import Config
from agent import IAIAgent
from schema import DatabaseManager

# ==================== Logging ====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class HealthEndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.args and len(record.args) >= 3 and record.args[2] != "/health"

logging.getLogger("uvicorn.access").addFilter(HealthEndpointFilter())

# ==================== App Initialization ====================

app = FastAPI(
    title="IAI — Incorrect Allocation Identifier",
    description=(
        "Rule-based agent API for validating employee resource allocation "
        "records against seven business rules (R1–R7). "
        "Generates structured exception reports for Resource Managers."
    ),
    version="2.0.0",
)

# CORS middleware — allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Dependency Injection ====================

# Singleton config and DB manager, initialized on startup
_config: Config = None
_db_manager: DatabaseManager = None


@app.on_event("startup")
def startup():
    """Initialize config and database connection on app startup."""
    global _config, _db_manager
    logger.info("Initializing IAI API server...")

    _config = Config()
    _config.load()

    _db_manager = DatabaseManager(db_url=_config.database_url)
    _db_manager.initialize_schema()

    logger.info("IAI API server ready.")


def get_config() -> Config:
    return _config


def get_db() -> DatabaseManager:
    return _db_manager


# ==================== Pydantic Models ====================

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    database_connected: bool = Field(..., description="Whether PostgreSQL is reachable")
    timestamp: str = Field(..., description="Current server timestamp")
    version: str = Field(default="2.0.0", description="API version")


class PipelineRequest(BaseModel):
    """Optional overrides for pipeline run."""
    ris_path: Optional[str] = Field(None, description="Override RIS file path")
    so_path: Optional[str] = Field(None, description="Override SO file path")


class PipelineResponse(BaseModel):
    run_id: int = Field(..., description="Database run ID")
    status: str = Field(..., description="Pipeline execution status")
    run_timestamp: str = Field(..., description="When the pipeline ran")
    total_records: int = Field(..., description="Total records evaluated")
    total_exceptions: int = Field(..., description="Total exceptions found")
    exception_counts: dict = Field(default_factory=dict, description="Exception counts by rule ID")
    report_path: Optional[str] = Field(None, description="Path to generated Excel report")
    error: Optional[str] = Field(None, description="Error message if pipeline failed")


class ExceptionRecord(BaseModel):
    exception_id: Optional[int] = None
    run_id: Optional[int] = None
    psid: Optional[str] = None
    employee_name: Optional[str] = None
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    exception_reason: Optional[str] = None
    severity: Optional[str] = None
    task_type: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    recommended_action: Optional[str] = None

    class Config:
        from_attributes = True


class ExceptionsResponse(BaseModel):
    total: int = Field(..., description="Number of records returned")
    exceptions: list = Field(default_factory=list, description="Exception records")


class RunRecord(BaseModel):
    run_id: Optional[int] = None
    run_timestamp: Optional[str] = None
    total_records_evaluated: Optional[int] = None
    total_exceptions: Optional[int] = None
    run_status: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class RunsResponse(BaseModel):
    total: int
    runs: list


class RejectedRowsResponse(BaseModel):
    total: int
    data: list


class SummaryResponse(BaseModel):
    run_id: int
    run_info: Optional[dict] = None
    by_rule: list = Field(default_factory=list)
    by_severity: list = Field(default_factory=list)


class DataFilesResponse(BaseModel):
    files: List[str]


# ==================== Endpoints ====================

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Basic health check — verifies API is running and DB is reachable."""
    db = get_db()
    return HealthResponse(
        status="ok",
        database_connected=db.is_connected() if db else False,
        timestamp=datetime.now().isoformat(),
    )

@app.get("/debug", tags=["System"])
def debug_check():
    return {"file": __file__}


# Global lock to prevent concurrent pipeline runs
_pipeline_lock = threading.Lock()

# Global progress tracker: { temp_id or run_id: { status, current_step, progress_pct, run_id, error_message, exception_count } }
_pipeline_progress = {}


def _run_pipeline_background(temp_id: str, config):
    """Execute pipeline in background thread, updating _pipeline_progress at each stage."""
    progress = _pipeline_progress[temp_id]
    
    def on_agent_progress(step, pct):
        progress.update({"current_step": step, "progress_pct": pct})

    try:
        agent = IAIAgent(config=config)
        result = agent.run(on_progress=on_agent_progress)

        # Mark completion
        if result["status"] == "error":
            progress.update({
                "status": "error",
                "current_step": "Failed",
                "progress_pct": 100,
                "run_id": result["run_id"],
                "error_message": result["error"],
                "exception_count": 0,
            })
        else:
            progress.update({
                "status": "success",
                "current_step": "Complete",
                "progress_pct": 100,
                "run_id": result["run_id"],
                "error_message": None,
                "exception_count": result["total_exceptions"],
            })
    except Exception as e:
        logger.error(f"Background pipeline failed: {e}", exc_info=True)
        progress.update({
            "status": "error",
            "current_step": "Failed",
            "progress_pct": 100,
            "error_message": str(e),
        })
    finally:
        _pipeline_lock.release()


@app.post("/api/trigger", tags=["Pipeline"])
def run_pipeline(request: PipelineRequest = None):
    """
    Trigger the full IAI agent pipeline in the background.

    Returns immediately with a temporary run reference.
    Use GET /api/run-status/{temp_id} to poll for progress.
    """
    if not _pipeline_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A pipeline run is already in progress.")

    config = get_config()

    # Apply optional overrides
    if request and request.ris_path:
        config.ris_path = request.ris_path
    if request and request.so_path:
        config.so_path = request.so_path

    # Generate a temp ID for tracking (will be replaced by real run_id when pipeline completes)
    temp_id = str(uuid.uuid4())[:8]

    _pipeline_progress[temp_id] = {
        "status": "running",
        "current_step": "Initializing pipeline",
        "progress_pct": 5,
        "run_id": None,
        "error_message": None,
        "exception_count": 0,
    }

    # Launch pipeline in background thread
    thread = threading.Thread(target=_run_pipeline_background, args=(temp_id, config), daemon=True)
    thread.start()

    return {
        "message": "Pipeline triggered successfully",
        "run_id": temp_id,
        "status": "running",
    }


@app.get("/api/exceptions", response_model=ExceptionsResponse, tags=["Exceptions"])
def get_exceptions(
    run_id: Optional[int] = Query(None, description="Filter by specific run ID"),
    limit: int = Query(500, ge=1, le=5000, description="Max records to return"),
    psid: Optional[str] = Query(None, description="Filter by specific PSID")
):
    """
    Fetch stored exception records from the database.

    Optionally filter by run_id or psid. Returns the most recent exceptions by default.
    """
    db = get_db()
    if not db or not db.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")

    exceptions = db.get_exceptions(run_id=run_id, limit=limit, psid=psid)

    # Serialize datetime objects
    for exc in exceptions:
        for key, val in exc.items():
            if hasattr(val, 'isoformat'):
                exc[key] = val.isoformat()

    return ExceptionsResponse(total=len(exceptions), exceptions=exceptions)


@app.get("/api/violations/top-violators", tags=["Exceptions"])
def get_top_violators(
    run_id: Optional[int] = Query(None, description="Filter by specific run ID"),
    limit: int = Query(10, ge=1, le=100, description="Max violators to return")
):
    """
    Fetch top violating employees aggregated from the database.
    """
    db = get_db()
    if not db or not db.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")

    violators = db.get_top_violators(run_id=run_id, limit=limit)
    return {"total": len(violators), "data": violators}



@app.get("/api/export-exceptions", tags=["Exceptions"])
def export_exceptions(run_id: int = Query(..., description="Run ID to export")):
    """Export exceptions for a specific run as a CSV file."""
    db = get_db()
    if not db or not db.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")

    exceptions = db.get_exceptions(run_id=run_id, limit=100000)
    if not exceptions:
        raise HTTPException(status_code=404, detail=f"No exceptions found for run_id={run_id}")

    # Create CSV in memory
    output = io.StringIO()
    if exceptions:
        # Use keys from first record as header
        fieldnames = list(exceptions[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for exc in exceptions:
            # Format datetime objects for CSV
            row = {}
            for k, v in exc.items():
                if hasattr(v, 'isoformat'):
                    row[k] = v.isoformat()
                else:
                    row[k] = v
            writer.writerow(row)

    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="iai_exceptions_run_{run_id}.csv"'
    }
    
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)

@app.get("/api/exceptions/{run_id}", response_model=ExceptionsResponse, tags=["Exceptions"])
def get_exceptions_by_run(run_id: int):
    """Fetch all exception records for a specific pipeline run."""
    db = get_db()
    if not db or not db.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")

    exceptions = db.get_exceptions(run_id=run_id)

    for exc in exceptions:
        for key, val in exc.items():
            if hasattr(val, 'isoformat'):
                exc[key] = val.isoformat()

    if not exceptions:
        raise HTTPException(status_code=404, detail=f"No exceptions found for run_id={run_id}")

    return ExceptionsResponse(total=len(exceptions), exceptions=exceptions)


@app.get("/api/runs", response_model=RunsResponse, tags=["Runs"])
def get_runs(limit: int = Query(50, ge=1, le=200, description="Max runs to return")):
    """Fetch run audit history (most recent first)."""
    db = get_db()
    if not db or not db.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")

    runs = db.get_runs(limit=limit)

    for run in runs:
        for key, val in run.items():
            if hasattr(val, 'isoformat'):
                run[key] = val.isoformat()

    return RunsResponse(total=len(runs), runs=runs)


@app.get("/api/run-status/{run_id}", tags=["Runs"])
def get_run_status(run_id: str):
    """
    Fetch the status of a pipeline run.
    
    Accepts either a temp_id (from the background trigger) or a numeric run_id.
    Returns current_step, progress_pct, status, error_message, exception_count.
    """
    # First check in-memory progress tracker (for background runs)
    if run_id in _pipeline_progress:
        progress = _pipeline_progress[run_id]
        return {
            "status": progress["status"],
            "current_step": progress["current_step"],
            "progress_pct": progress["progress_pct"],
            "run_id": progress["run_id"],
            "error_message": progress["error_message"],
            "exception_count": progress.get("exception_count", 0),
        }

    # Fallback: query database for completed runs
    db = get_db()
    if not db or not db.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
        
    try:
        numeric_id = int(run_id)
        with db.engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(
                text("SELECT run_status, error_message, total_exceptions FROM iai_run_audit WHERE run_id = :run_id"),
                {"run_id": numeric_id}
            ).fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")
                
            return {
                "status": result[0],
                "current_step": "Complete" if result[0] == "success" else "Failed",
                "progress_pct": 100,
                "run_id": numeric_id,
                "error_message": result[1],
                "exception_count": result[2] or 0,
            }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching run status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rejected", response_model=RejectedRowsResponse, tags=["Exceptions"])
def get_rejected_rows(run_id: Optional[int] = Query(None, description="Filter by run ID")):
    """Fetch rejected rows from the database."""
    db = get_db()
    if not db or not db.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
        
    try:
        with db.engine.connect() as conn:
            from sqlalchemy import text
            if run_id is not None:
                query = text("""
                    SELECT 
                        row_index, 
                        source_system AS source, 
                        rejection_reason AS reason, 
                        raw_data 
                    FROM iai_rejected_rows 
                    WHERE run_id = :run_id 
                    ORDER BY rejection_id
                """)
                result = conn.execute(query, {"run_id": run_id})
            else:
                query = text("""
                    SELECT 
                        row_index, 
                        source_system AS source, 
                        rejection_reason AS reason, 
                        raw_data 
                    FROM iai_rejected_rows 
                    WHERE run_id = (SELECT MAX(run_id) FROM iai_run_audit WHERE run_status IN ('success', 'no_exceptions'))
                    ORDER BY rejection_id DESC LIMIT 500
                """)
                result = conn.execute(query)
                
            rows = result.mappings().all()
            return RejectedRowsResponse(total=len(rows), data=[dict(r) for r in rows])
    except Exception as e:
        logger.error(f"Error fetching rejected rows: {e}")
        return RejectedRowsResponse(total=0, data=[])


@app.get("/api/summary/{run_id}", response_model=SummaryResponse, tags=["Summary"])
def get_summary(run_id: int):
    """
    Get summary statistics for a specific run.

    Returns counts grouped by rule and by severity.
    """
    db = get_db()
    if not db or not db.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")

    summary = db.get_summary(run_id=run_id)
    if not summary or not summary.get("run_info"):
        raise HTTPException(status_code=404, detail=f"No data found for run_id={run_id}")

    # Serialize datetime objects in nested dicts
    if summary.get("run_info"):
        for key, val in summary["run_info"].items():
            if hasattr(val, 'isoformat'):
                summary["run_info"][key] = val.isoformat()

    return SummaryResponse(**summary)


@app.get("/api/data-files", response_model=DataFilesResponse, tags=["System"])
def get_data_files():
    """List all .xlsx files in the Data directory."""
    import os
    data_dir = "Data"
    if not os.path.exists(data_dir):
        return DataFilesResponse(files=[])
    
    files = [f for f in os.listdir(data_dir) if f.endswith(".xlsx")]
    return DataFilesResponse(files=sorted(files))


@app.get("/config", tags=["System"])
def get_config_endpoint():
    """Return the current agent configuration (read-only)."""
    config = get_config()
    if not config:
        raise HTTPException(status_code=503, detail="Configuration not loaded")
    
    config_dict = config.to_dict()
    
    # Parse db_host and db_name from the redacted database_url
    db_url_part = config_dict.get("database_url", "")
    db_host = "localhost"
    db_name = "iai_db"
    if db_url_part:
        # Format after redaction: "host:port/dbname"
        if "/" in db_url_part:
            db_host = db_url_part.split("/")[0]
            db_name = db_url_part.split("/")[-1]
    
    return {
        "psid_field_name": config_dict.get("psid_field_name", "Emplid"),
        "contractor_codes": config_dict.get("contractor_codes", []),
        "support_sales_roles": config_dict.get("support_sales_roles", []),
        "notification_endpoint": config_dict.get("rm_notification_url", "Not configured"),
        "db_host": db_host,
        "db_name": db_name,
    }

# ==================== Main ====================

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Checking 127.0.0.1 specifically as 'localhost' can sometimes resolve to IPv6 ::1
        return s.connect_ex(('127.0.0.1', port)) == 0

if __name__ == "__main__":
    import uvicorn
    port = 8000
    while is_port_in_use(port):
        logger.info(f"Port {port} is in use, trying {port + 1}...")
        port += 1
    
    logger.info(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
