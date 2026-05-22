from backend.graph.state import FDAState
from backend.logger import logger

def decision_node(state: FDAState) -> FDAState:
    """
    Evaluates rule results and sets the decision_flag.
    If ANY project has junior_gap > 0 or triggers R1/R2, we route to LLM.
    """
    logger.info("--- NODE: decision_node ---")
    df = state.rule_results
    
    if df is None:
        logger.error("No rule results found")
        state.decision_flag = False
        return state
        
    # Check if any project has junior gap or triggered R1/R2
    needs_llm = False
    
    for _, row in df.iterrows():
        junior_gap = float(row.get('junior_gap', 0))
        r1_flag = bool(row.get('R1', False))
        r2_flag = bool(row.get('R2', False))
        
        if junior_gap > 0 or r1_flag or r2_flag:
            needs_llm = True
            break
            
    state.decision_flag = needs_llm
    logger.info(f"Decision Flag set to: {needs_llm}")
    return state
