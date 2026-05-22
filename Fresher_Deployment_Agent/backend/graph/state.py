from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Any, Optional

class FDAState(BaseModel):
    """
    Shared state for the FDA LangGraph.
    Uses arbitrary_types_allowed to permit passing Pandas DataFrames between deterministic nodes.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # ── Input Data ──────────────────────────────────────────────
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    
    # ── Processing Pipeline ─────────────────────────────────────
    validated_data: Optional[Any] = None
    processed_data: Optional[Any] = None
    aggregated_data: Optional[Any] = None
    pyramid_metrics: Optional[Any] = None
    rule_results: Optional[Any] = None
    
    # ── Routing & Decision ──────────────────────────────────────
    decision_flag: bool = False
    
    # ── LLM Outputs (Strict Dicts, NO DataFrames) ───────────────
    r3_output: Dict[str, Any] = Field(default_factory=dict)
    r4_output: Dict[str, Any] = Field(default_factory=dict)
    
    # ── Final Results ───────────────────────────────────────────
    recommendations: Optional[Any] = None
    outputs: Dict[str, str] = Field(default_factory=dict)
