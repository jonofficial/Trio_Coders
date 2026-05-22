from backend.graph.state import FDAState
from backend.llm_agents import sanitize_project_data, generate_training_suggestions
from backend.services.recommendation_engine import extract_skills_for_project
from backend.logger import logger

def r4_llm_node(state: FDAState) -> FDAState:
    logger.info("--- NODE: r4_llm_node ---")
    df = state.rule_results
    so_df = state.raw_data.get("so")
    ris_df = state.raw_data.get("ris")
    r3_outputs = state.r3_output
    
    if df is None:
        return state
        
    so_skill_cols = ['technology', 'skills', 'secondary_skills']
    ris_skill_cols = ['technology', 'skills']
    
    r4_outputs = {}
    
    for _, row in df.iterrows():
        project_name = row['project_name']
        r3_result = r3_outputs.get(project_name, {})
        
        # Trigger R4 if R3 says suitable for fresher OR R2 is flagged
        is_suitable = r3_result.get("suitable_for_fresher", False)
        is_high_intake = bool(row.get('R2', False))
        
        if is_suitable or is_high_intake:
            project_ids = row.get('project_id_list', [row.get('project_id', 'N/A')])
            ris_skills = extract_skills_for_project(ris_df, project_ids, project_name, ris_skill_cols)
            so_skills = extract_skills_for_project(so_df, project_ids, project_name, so_skill_cols)
            
            sanitized_data = sanitize_project_data(row, ris_skills, so_skills)
            r4_result = generate_training_suggestions(sanitized_data)
            
            r4_outputs[project_name] = r4_result
            
    state.r4_output = r4_outputs
    return state
