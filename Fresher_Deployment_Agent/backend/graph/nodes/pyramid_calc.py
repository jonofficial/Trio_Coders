import pandas as pd
from backend.graph.state import FDAState
from backend import settings
from backend.logger import logger

def pyramid_calc_node(state: FDAState) -> FDAState:
    logger.info("--- NODE: pyramid_calc_node ---")
    agg_df = state.aggregated_data
    
    if agg_df is None:
        logger.error("No aggregated data found")
        return state
        
    df = agg_df.copy()
    total = df['total_headcount'].replace(0, pd.NA)
    
    df['junior_pct']  = (df['junior_count']  / total * 100).round(2)
    df['mid_pct']     = (df['mid_count']     / total * 100).round(2)
    df['senior_pct']  = (df['senior_count']  / total * 100).round(2)
    
    df['junior_gap']  = (settings.TARGET_JUNIOR_PCT - df['junior_pct']).round(2)
    df['mid_gap']     = (settings.TARGET_MID_PCT    - df['mid_pct']   ).round(2)
    df['senior_gap']  = (settings.TARGET_SENIOR_PCT - df['senior_pct']).round(2)
    
    df['over_indexed_mid']    = df['mid_pct']    > settings.TARGET_MID_PCT
    df['over_indexed_senior'] = df['senior_pct'] > settings.TARGET_SENIOR_PCT
    
    state.pyramid_metrics = df
    return state
