from backend.services.rule_engine.base import Rule
import pandas as pd
from backend import settings

class R1LowJuniorRatio(Rule):
    """
    R1: Low Junior Ratio
    Triggered when Junior % < Target Junior % (default 79%)
    """
    
    @property
    def rule_id(self) -> str:
        return "R1"
        
    @property
    def description(self) -> str:
        return f"Junior % is below the target of {settings.TARGET_JUNIOR_PCT}%"
        
    def evaluate(self, project_data: pd.Series, *args, **kwargs) -> bool:
        junior_pct = project_data.get('junior_pct', 0)
        return junior_pct < settings.TARGET_JUNIOR_PCT
