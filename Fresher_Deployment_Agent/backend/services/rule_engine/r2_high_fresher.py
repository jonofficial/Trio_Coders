from backend.services.rule_engine.base import Rule
import pandas as pd
from backend import settings

class R2HighFresherIntake(Rule):
    """
    R2: High Fresher Intake
    Triggered when the junior ratio is disproportionately high relative to team size.
    Two conditions (either triggers the flag):
    1. Junior% > R2_HIGH_FRESHER_THRESHOLD_PCT (default 85%)
    2. Small team with majority juniors: team_size <= R2_SMALL_TEAM_THRESHOLD and junior_count >= 2/3 of team
    """
    
    @property
    def rule_id(self) -> str:
        return "R2"
        
    @property
    def description(self) -> str:
        return (
            f"High junior ratio relative to team size "
            f"(Junior% > {settings.R2_HIGH_FRESHER_THRESHOLD_PCT}%) "
            f"OR small team with disproportionately high junior headcount."
        )
        
    def evaluate(self, project_data: pd.Series, *args, **kwargs) -> bool:
        junior_pct = float(project_data.get('junior_pct', 0))
        total_hc = int(project_data.get('total_headcount', 0))
        junior_count = int(project_data.get('junior_count', 0))
        
        # Condition 1: Junior % exceeds high threshold
        if junior_pct > settings.R2_HIGH_FRESHER_THRESHOLD_PCT:
            return True
        
        # Condition 2: Small team (<=10 people) where more than 2/3 are juniors
        small_team_threshold = settings.R2_SMALL_TEAM_THRESHOLD
        if total_hc <= small_team_threshold and total_hc > 0:
            if (junior_count / total_hc) >= settings.R2_SMALL_TEAM_JUNIOR_RATIO:
                return True
        
        return False
