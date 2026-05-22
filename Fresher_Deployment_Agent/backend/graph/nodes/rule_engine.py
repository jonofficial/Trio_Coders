from backend.graph.state import FDAState
from backend.services.rule_engine.r1_low_junior import R1LowJuniorRatio
from backend.services.rule_engine.r2_high_fresher import R2HighFresherIntake
from backend.logger import logger

def rule_engine_node(state: FDAState) -> FDAState:
    logger.info("--- NODE: rule_engine_node ---")
    df = state.pyramid_metrics
    
    if df is None:
        logger.error("No pyramid metrics found")
        return state
        
    r1 = R1LowJuniorRatio()
    r2 = R2HighFresherIntake()
    
    df = df.copy()
    
    flags = []
    r1_col = []
    r2_col = []
    
    for _, row in df.iterrows():
        is_r1 = r1.evaluate(row)
        is_r2 = r2.evaluate(row)
        
        r1_col.append(is_r1)
        r2_col.append(is_r2)
        
        project_flags = []
        if is_r1: project_flags.append('Low Junior Warning')
        if is_r2: project_flags.append('High Fresher Intake')
        
        flags.append(' | '.join(project_flags) if project_flags else 'Healthy')
        
    df['R1'] = r1_col
    df['R2'] = r2_col
    df['flags'] = flags
    
    state.rule_results = df
    return state
