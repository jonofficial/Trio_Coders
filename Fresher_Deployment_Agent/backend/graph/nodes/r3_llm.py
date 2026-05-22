from backend.graph.state import FDAState
from backend.llm_agents import sanitize_project_data, analyze_deployment_opportunity
from backend.services.recommendation_engine import extract_skills_for_project
from backend.logger import logger

def r3_llm_node(state: FDAState) -> FDAState:
    logger.info("--- NODE: r3_llm_node ---")
    df = state.rule_results
    so_df = state.raw_data.get("so")
    ris_df = state.raw_data.get("ris")
    
    if df is None or so_df is None or ris_df is None:
        logger.error("Missing data for R3 LLM node")
        return state
        
    so_skill_cols = ['technology', 'skills', 'secondary_skills']
    ris_skill_cols = ['technology', 'skills']
    
    r3_outputs = {}
    
    for _, row in df.iterrows():
        project_name = row['project_name']
        junior_gap = float(row.get('junior_gap', 0))
        
        if junior_gap <= 0:
            continue # No fresher deployment needed
            
        project_ids = row.get('project_id_list', [row.get('project_id', 'N/A')])
        logger.info(f"Project IDs for {project_name}: {project_ids}")
        ris_skills = extract_skills_for_project(ris_df, project_ids, project_name, ris_skill_cols)
        so_skills = extract_skills_for_project(so_df, project_ids, project_name, so_skill_cols)
        
        sanitized_data = sanitize_project_data(row, ris_skills, so_skills)
        
        # Call LLM
        r3_result = analyze_deployment_opportunity(sanitized_data)
        
        # User Override: Assume the fresher can handle it regardless of LLM evaluation
        # This ensures R4 (Training Suggestions) always runs for projects with a gap
        r3_result["suitable_for_fresher"] = True
        
        # Calculate Strict Readiness Score
        # weights: Gap(40%), Skill(30%), Team Size(20%), Role Match(10%)
        normalized_gap = min(1.0, junior_gap / 50.0) # Assume 50% gap is max normalized
        skill_overlap = r3_result.get("skill_overlap_score", 0.0)
        role_match = r3_result.get("role_match_score", 0.5)
        
        team_size = sanitized_data["team_size"]
        team_size_factor = min(1.0, team_size / 50.0) # Larger teams can absorb freshers better
        
        score_base = (0.4 * normalized_gap) + (0.3 * skill_overlap) + (0.2 * team_size_factor) + (0.1 * role_match)
        score = score_base * 100.0
        r3_result["deployment_readiness_score"] = min(100.0, round(score, 2))
        
        r3_outputs[project_name] = r3_result
        
    state.r3_output = r3_outputs
    return state
