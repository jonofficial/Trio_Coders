import pandas as pd
import math
from backend.logger import logger
from backend import settings

def extract_skills_for_project(df: pd.DataFrame, project_id: str, project_name: str, skill_cols: list) -> set:
    """
    Extracts dominant skills from multiple skill columns for a given project.
    Parses comma-separated skills in each column and returns the top-N most frequent.
    """
    proj_data = pd.DataFrame()
    
    def clean_id(pid):
        if pd.isna(pid) or pid == 'N/A': return 'N/A'
        val = str(pid).strip()
        return val[:-2] if val.endswith('.0') else val

    if not isinstance(project_id, list):
        project_ids = [project_id]
    else:
        project_ids = project_id
        
    cleaned_target_ids = [clean_id(pid) for pid in project_ids if clean_id(pid) != 'N/A']

    if 'project_id' in df.columns and cleaned_target_ids:
        proj_data = df[df['project_id'].apply(clean_id).isin(cleaned_target_ids)]
    
    if proj_data.empty and 'project_name' in df.columns and pd.notna(project_name) and project_name != 'N/A':
        proj_data = df[df['project_name'].astype(str).str.strip() == str(project_name).strip()]
    
    if proj_data.empty:
        return set()
    
    all_skills = []
    for col in skill_cols:
        if col not in proj_data.columns:
            continue
        for skill_str in proj_data[col].dropna():
            skills = [s.strip().upper() for s in str(skill_str).split(',') if s.strip()]
            all_skills.extend(skills)
    
    if not all_skills:
        return set()
    
    skill_counts = pd.Series(all_skills).value_counts()
    top_skills = set(skill_counts.head(5).index.tolist())
    return top_skills


def generate_recommendations(decided_df: pd.DataFrame, ris_data: pd.DataFrame, so_data: pd.DataFrame) -> pd.DataFrame:
    """
    Generates Deployment & Training Suggestions Report.
    
    For R3: Uses SO data (Technology + Primary Skill + Secondary Skill) for role compatibility.
    For R4: Combines RIS (technology + skills) + SO (technology + primary + secondary) skill themes.
    """
    logger.info("Generating deployment and training recommendations.")
    
    # SO skill columns: Technology, Primary Skill Description, Secondary Skill Description
    so_skill_cols = ['technology', 'skills', 'secondary_skills']
    
    # RIS skill columns: TalentX Core Skill (technology) + TalentX Primary & Secondary Skills (skills)
    ris_skill_cols = ['technology', 'skills']
    
    recommendations = []
    
    for _, row in decided_df.iterrows():
        project_name = row['project_name']
        project_id = row.get('project_id', 'N/A')
        total_hc = int(row.get('total_headcount', 0))
        junior_gap_pct = float(row.get('junior_gap', 0))
        r3_flag = bool(row.get('R3', False))
        r4_flag = bool(row.get('R4', False))
        
        # ── Suggested Fresher Count ──────────────────────────────────────────
        # How many people to close the junior gap
        suggested_fresher_count = 0
        if junior_gap_pct > 0 and total_hc > 0:
            suggested_fresher_count = math.ceil((junior_gap_pct / 100.0) * total_hc)
        
        # ── Extract skills from SO (Relevant Technologies for deployment) ────
        so_skills = extract_skills_for_project(so_data, project_id, project_name, so_skill_cols)
        
        # ── Extract skills from RIS (Primary Skills Present) ─────────────────
        ris_skills = extract_skills_for_project(ris_data, project_id, project_name, ris_skill_cols)
        
        relevant_skills = ", ".join(so_skills) if so_skills else "N/A"
        primary_skills_present = ", ".join(ris_skills) if ris_skills else "N/A"
        
        # ── Training Theme (R4): Combine SO demand + RIS existing skills ─────
        training_theme = "N/A"
        training_flag = "NO"
        
        if r4_flag:
            training_flag = "YES"
            # Union of SO demanded skills and current RIS skills → training roadmap
            all_skills = ris_skills.union(so_skills)
            if all_skills:
                training_theme = f"Foundational training on: {', '.join(all_skills)}"
            else:
                training_theme = "General Fresher Onboarding & Project Orientation"
        
        # ── Deployment Readiness Score ─────────────────────────────────────────
        # Basic dynamic scoring if no LLM: calculate based on gap size & skill match
        base_score = 50.0
        if r3_flag:
            base_score += 20.0
        if ris_skills.intersection(so_skills):
            base_score += 20.0
        if junior_gap_pct > 20:
            base_score += 10.0
        readiness_score = min(100.0, base_score)

        recommendations.append({
            'project_id': project_id,
            'project_name': project_name,
            'junior_pct': round(float(row.get('junior_pct', 0)), 2),
            'junior_gap': round(junior_gap_pct, 2),
            'pyramid_health': row.get('flags', 'Healthy / Monitoring'),
            'deployment_flag': 'Yes' if r3_flag else 'No',
            'suggested_fresher_count': suggested_fresher_count if r3_flag else 0,
            'relevant_skills': relevant_skills,
            'primary_skills': primary_skills_present,
            'training_suggestions': training_theme,
            'training_flag': training_flag,
            'deployment_readiness_score': readiness_score
        })
    
    rec_df = pd.DataFrame(recommendations)
    logger.info("Recommendation generation complete.")
    return rec_df
