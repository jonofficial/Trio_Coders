from backend.services.rule_engine.base import Rule
import pandas as pd

class R4TrainingSuggestions(Rule):
    """
    R4: Training Suggestions
    Triggered for all projects that are deployment candidates (R3 = True).
    Also triggered if the project has a high fresher intake (R2 = True),
    since freshers already there likely need training.
    
    The actual training themes are computed in the recommendation engine using:
    - Technology column
    - Primary Skill Description  
    - Secondary Skill Description
    """
    
    @property
    def rule_id(self) -> str:
        return "R4"
        
    @property
    def description(self) -> str:
        return (
            "Training suggestions required: project is a deployment candidate (R3) "
            "or has disproportionate junior intake (R2)."
        )
        
    def evaluate(self, project_data: pd.Series, *args, **kwargs) -> bool:
        junior_gap = float(project_data.get('junior_gap', 0))
        junior_pct = float(project_data.get('junior_pct', 0))
        
        # R4 fires if project needs freshers (gap > 0) OR already has too many freshers (high intake)
        # In both cases, training for the deployed/to-be-deployed freshers is required
        return junior_gap > 0 or junior_pct > 85.0
