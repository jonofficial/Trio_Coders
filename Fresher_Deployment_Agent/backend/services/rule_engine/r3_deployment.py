from backend.services.rule_engine.base import Rule
import pandas as pd

# Entry-level compatible roles and technologies
ENTRY_LEVEL_ROLES = {
    "developer", "associate", "trainee", "analyst", "engineer",
    "junior", "fresher", "intern", "graduate", "tester", "qa"
}

ENTRY_LEVEL_TECHNOLOGIES = {
    "python", "java", "sql", "javascript", "testing", "manual testing",
    "html", "css", "selenium", "git", "excel", "data entry", ".net", "angular",
    "react", "node", "automation"
}

def _is_entry_level_compatible(project_id: str, so_data: pd.DataFrame) -> bool:
    """
    Checks if the SO data for a project contains at least one role or skill
    that is compatible with entry-level / fresher deployment.
    """
    if so_data is None or so_data.empty:
        return False
        
    proj_so = so_data[so_data['project_id'] == project_id] if 'project_id' in so_data.columns else pd.DataFrame()
    
    if proj_so.empty:
        return False
    
    # Check Project Role column
    if 'project_role' in proj_so.columns:
        for role in proj_so['project_role'].dropna():
            if any(kw in str(role).lower() for kw in ENTRY_LEVEL_ROLES):
                return True
    
    # Check Technology column
    if 'technology' in proj_so.columns:
        for tech in proj_so['technology'].dropna():
            if any(kw in str(tech).lower() for kw in ENTRY_LEVEL_TECHNOLOGIES):
                return True
    
    # Check Primary Skill Description
    if 'skills' in proj_so.columns:
        for skill in proj_so['skills'].dropna():
            if any(kw in str(skill).lower() for kw in ENTRY_LEVEL_TECHNOLOGIES):
                return True
    
    return False


class R3FresherDeployment(Rule):
    """
    R3: Fresher Deployment Opportunity
    A project qualifies as a deployment candidate if:
    (a) It is junior-deficit (Junior Gap > 0) — per R1 condition
    (b) At least one role/skill on the SO data for the project is entry-level compatible
    Both conditions must be true.
    """
    
    @property
    def rule_id(self) -> str:
        return "R3"
        
    @property
    def description(self) -> str:
        return (
            "Project is junior-deficit (Junior Gap > 0) AND has at least one "
            "entry-level compatible role/skill in SO data."
        )
        
    def evaluate(self, project_data: pd.Series, *args, **kwargs) -> bool:
        junior_gap = float(project_data.get('junior_gap', 0))
        project_id = project_data.get('project_id', '')
        so_data = kwargs.get('so_data', None)
        
        # Condition (a): junior-deficit
        if junior_gap <= 0:
            return False
        
        # Condition (b): entry-level role/skill compatibility from SO
        return _is_entry_level_compatible(project_id, so_data)
