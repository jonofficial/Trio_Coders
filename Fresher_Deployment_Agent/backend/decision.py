import pandas as pd
from backend.services.rule_engine import ACTIVE_RULES
from backend.logger import logger

def execute_rules(agg_df: pd.DataFrame, so_data: pd.DataFrame = None) -> pd.DataFrame:
    """
    Executes all active rules against the aggregated project data.
    Adds a column for each rule's boolean output, plus a 'flags' column.
    """
    logger.info("Executing decision engine rules.")
    
    result_df = agg_df.copy()
    flags_list = []
    
    for _, row in result_df.iterrows():
        project_flags = []
        for rule in ACTIVE_RULES:
            # evaluate rule
            triggered = rule.evaluate(row, so_data=so_data)
            
            # Store individual rule outcome (e.g., column 'R1')
            result_df.at[_, rule.rule_id] = triggered
            
            if triggered:
                project_flags.append(rule.rule_id)
                logger.debug(f"Project {row['project_id']} triggered rule {rule.rule_id}")
                
        flags_list.append(", ".join(project_flags) if project_flags else "Healthy / Monitoring")
        
    result_df['flags'] = flags_list
    logger.info("Rule execution complete.")
    return result_df
