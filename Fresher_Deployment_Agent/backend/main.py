import sys
import os
import glob
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# __file__ is now backend/main.py — we need the project root on sys.path
# so that 'backend' is resolvable as a top-level package.
BASE_DIR = Path(__file__).resolve().parent   # backend/
ROOT_DIR = BASE_DIR.parent                  # project root
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.logger import logger
from backend.graph.graph_builder import build_fda_graph
from backend.graph.state import FDAState
from backend import settings

# Initialize FastAPI app
app = FastAPI(
    title="Fresher Deployment Agent (FDA) API",
    description="API for triggering the FDA pipeline",
    version="1.0.0"
)

# CORS middleware — allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the output directory as static files so the frontend can fetch Excel reports
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="output")


def run_fda_pipeline() -> dict:
    """Core pipeline logic. Returns status and output file paths."""
    logger.info("Starting Fresher Deployment Agent (FDA) Pipeline...")

    try:
        # Compile Graph
        logger.info("Building LangGraph...")
        graph = build_fda_graph()

        # Initialize State
        initial_state = FDAState()

        # Run Graph
        logger.info("Executing LangGraph Pipeline...")
        final_state = graph.invoke(initial_state)

        logger.info("LangGraph Pipeline completed successfully.")

        # Find the latest output files by timestamp
        pyramid_files = sorted(glob.glob(str(settings.OUTPUT_DIR / "FDA_PyramidReport_*.xlsx")), reverse=True)
        suggestions_files = sorted(glob.glob(str(settings.OUTPUT_DIR / "FDA_Suggestions_*.xlsx")), reverse=True)

        pyramid_path = f"/output/{Path(pyramid_files[0]).name}" if pyramid_files else None
        suggestions_path = f"/output/{Path(suggestions_files[0]).name}" if suggestions_files else None

        return {
            "pyramid_path": pyramid_path,
            "suggestions_path": suggestions_path,
        }

    except Exception as e:
        logger.exception(f"FDA Pipeline failed with error: {str(e)}")
        return {
            "pyramid_path": None,
            "suggestions_path": None,
        }


@app.get("/")
def read_root():
    return {"message": "FDA API is running. Go to /docs to view the Swagger UI."}


@app.post("/run-pipeline")
def trigger_pipeline():
    """Runs the FDA analysis pipeline synchronously and returns output file paths."""
    result = run_fda_pipeline()
    return result


def start():
    """Entry point for the application."""
    logger.info("Starting FDA API Server...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    start()
