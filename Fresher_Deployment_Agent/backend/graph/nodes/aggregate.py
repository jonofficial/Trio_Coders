import pandas as pd
from backend.graph.state import FDAState
from backend.logger import logger

def aggregate_node(state: FDAState) -> FDAState:
    logger.info("--- NODE: aggregate_node ---")
    df = state.processed_data
    
    if df is None:
        logger.error("No processed data found")
        return state
        
    if 'project_name' not in df.columns or 'band' not in df.columns:
        logger.error("Missing required columns ('project_name' or 'band')")
        return state
        
    agg_cols = {'total_headcount': ('project_name', 'count')}
    if 'project_id' in df.columns:
        agg_cols['project_id'] = ('project_id', 'first')
        agg_cols['project_id_list'] = ('project_id', lambda x: list(set(x)))
    if 'rm' in df.columns:
        agg_cols['rm'] = ('rm', 'first')
        
    agg_df = df.groupby('project_name').agg(**agg_cols).reset_index()
    
    band_counts = (
        df.groupby(['project_name', 'band'])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    
    agg_df = pd.merge(agg_df, band_counts, on='project_name', how='left')
    
    for band_label, col_name in [('Junior', 'junior_count'), ('Mid', 'mid_count'), ('Senior', 'senior_count')]:
        if band_label in agg_df.columns:
            agg_df.rename(columns={band_label: col_name}, inplace=True)
        else:
            agg_df[col_name] = 0
            
    state.aggregated_data = agg_df
    return state
