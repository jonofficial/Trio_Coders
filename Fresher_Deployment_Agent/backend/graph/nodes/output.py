from backend.graph.state import FDAState
from backend.exporter import export_pyramid_report, export_suggestions_report
from backend.logger import logger

def output_node(state: FDAState) -> FDAState:
    logger.info("--- NODE: output_node ---")
    
    if state.rule_results is not None:
        export_pyramid_report(state.rule_results)
        
    if state.recommendations is not None and state.raw_data.get("ris") is not None:
        export_suggestions_report(state.recommendations, state.raw_data.get("ris"))
        
    return state
