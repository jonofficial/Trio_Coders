from backend.graph.state import FDAState
from backend.ingestion import load_ris_data, load_so_data
from backend.logger import logger

def ingest_node(state: FDAState) -> FDAState:
    logger.info("--- NODE: ingest_node ---")
    ris_df = load_ris_data()
    so_df = load_so_data()
    
    state.raw_data = {
        "ris": ris_df,
        "so": so_df
    }
    return state
