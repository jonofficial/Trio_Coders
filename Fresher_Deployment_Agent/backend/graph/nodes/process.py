from backend.graph.state import FDAState
from backend.validation import map_grades_to_bands, load_grade_band_map
from backend.logger import logger

def process_node(state: FDAState) -> FDAState:
    logger.info("--- NODE: process_node ---")
    valid_ris = state.validated_data
    
    if valid_ris is not None:
        grade_map = load_grade_band_map()
        processed_ris = map_grades_to_bands(valid_ris, grade_map)
        state.processed_data = processed_ris
    else:
        logger.error("No validated data found")
        
    return state
