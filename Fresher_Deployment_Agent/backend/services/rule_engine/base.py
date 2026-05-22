from abc import ABC, abstractmethod
import pandas as pd

class Rule(ABC):
    """Base class for all rules in the system."""
    
    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for the rule (e.g., 'R1')."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Human readable description of the rule."""
        pass
        
    @abstractmethod
    def evaluate(self, project_data: pd.Series, *args, **kwargs) -> bool:
        """
        Evaluates the rule against a single project's aggregated data.
        Returns True if the rule condition is met (e.g., if a flag should be raised).
        """
        pass
