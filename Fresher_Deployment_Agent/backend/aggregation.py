import pandas as pd
from backend import settings
from backend.logger import logger

def aggregate_by_project(df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups data by Project ID and computes:
    - total headcount (distinct employees counted once per project)
    - junior count, mid count, senior count
    - ratios for each band (Junior%, Mid%, Senior%)
    - gaps for each band vs target pyramid (79/20/1)
    - over-indexed flags for Mid and Senior
    """
    logger.info("Aggregating data by Project ID.")
    
    if 'project_name' not in df.columns or 'band' not in df.columns:
        logger.error("Missing required columns ('project_name' or 'band') for aggregation.")
        return pd.DataFrame()
    
    # ── Basic aggregation: headcount + project metadata ─────────────────────
    agg_cols = {'total_headcount': ('project_name', 'count')}
    if 'project_id' in df.columns:
        agg_cols['project_id'] = ('project_id', 'first')
        agg_cols['project_id_list'] = ('project_id', lambda x: list(set(x)))
    if 'rm' in df.columns:
        agg_cols['rm'] = ('rm', 'first')
    
    agg_df = df.groupby('project_name').agg(**agg_cols).reset_index()
    
    # ── Band counts: pivot band column per project ───────────────────────────
    band_counts = (
        df.groupby(['project_name', 'band'])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    
    # Merge band counts
    agg_df = pd.merge(agg_df, band_counts, on='project_name', how='left')
    
    # Normalise band column names
    for band_label, col_name in [('Junior', 'junior_count'), ('Mid', 'mid_count'), ('Senior', 'senior_count')]:
        if band_label in agg_df.columns:
            agg_df.rename(columns={band_label: col_name}, inplace=True)
        else:
            agg_df[col_name] = 0
    
    # ── Ratios (PDF formula: JuniorCount / TotalActiveHead * 100) ───────────
    total = agg_df['total_headcount'].replace(0, pd.NA)  # avoid division by zero
    agg_df['junior_pct']  = (agg_df['junior_count']  / total * 100).round(2)
    agg_df['mid_pct']     = (agg_df['mid_count']     / total * 100).round(2)
    agg_df['senior_pct']  = (agg_df['senior_count']  / total * 100).round(2)
    
    # ── Gaps (79 − Actual%, 20 − Actual%, 1 − Actual%) ──────────────────────
    agg_df['junior_gap']  = (settings.TARGET_JUNIOR_PCT - agg_df['junior_pct']).round(2)
    agg_df['mid_gap']     = (settings.TARGET_MID_PCT    - agg_df['mid_pct']   ).round(2)
    agg_df['senior_gap']  = (settings.TARGET_SENIOR_PCT - agg_df['senior_pct']).round(2)
    
    # ── Over-indexed flags ───────────────────────────────────────────────────
    # Mid is over-indexed if Mid% > 20; Senior if Senior% > 1
    agg_df['over_indexed_mid']    = agg_df['mid_pct']    > settings.TARGET_MID_PCT
    agg_df['over_indexed_senior'] = agg_df['senior_pct'] > settings.TARGET_SENIOR_PCT
    
    logger.info(f"Aggregation complete for {len(agg_df)} projects.")
    return agg_df
