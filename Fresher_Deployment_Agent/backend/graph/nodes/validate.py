from backend.graph.state import FDAState
from backend.validation import filter_active_resources
from backend import settings
from backend.logger import logger

def validate_node(state: FDAState) -> FDAState:
    logger.info("--- NODE: validate_node ---")
    ris_df = state.raw_data.get("ris")
    
    if ris_df is not None:
        valid_ris = filter_active_resources(ris_df)
        
        # Ensure required columns are present
        for col in settings.RIS_REQUIRED_COLS:
            if col not in valid_ris.columns:
                valid_ris[col] = "N/A"
                
        state.validated_data = valid_ris
    else:
        logger.error("No RIS data found in raw_data")
        
    return state
