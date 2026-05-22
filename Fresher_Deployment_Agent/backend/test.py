import pytest
import pandas as pd
from backend.aggregation import aggregate_by_project
from backend.decision import execute_rules
from backend.services.recommendation_engine import generate_recommendations
from backend.services.rule_engine.r1_low_junior import R1LowJuniorRatio
from backend.services.rule_engine.r2_high_fresher import R2HighFresherIntake
from backend.services.rule_engine.r3_deployment import R3FresherDeployment
from backend import settings

# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def sample_ris_data():
    return pd.DataFrame([
        {'employee_id': '1', 'project_id': 'P1', 'band': 'Junior', 'skills': 'Python, SQL'},
        {'employee_id': '2', 'project_id': 'P1', 'band': 'Mid', 'skills': 'Python'},
        {'employee_id': '3', 'project_id': 'P2', 'band': 'Junior', 'skills': 'Java'},
    ])

@pytest.fixture
def sample_so_data():
    return pd.DataFrame([
        {'project_id': 'P1', 'skills': 'Python, AWS'},
        {'project_id': 'P2', 'skills': 'Java, Spring'}
    ])

# ── Pipeline Tests ─────────────────────────────────────────────────────────

def test_aggregation(sample_ris_data):
    agg_df = aggregate_by_project(sample_ris_data)
    assert len(agg_df) == 2
    p1 = agg_df[agg_df['project_id'] == 'P1'].iloc[0]
    assert p1['total_headcount'] == 2
    assert p1['junior_count'] == 1
    assert p1['junior_pct'] == 50.0

def test_decision_engine(sample_ris_data, sample_so_data):
    agg_df = aggregate_by_project(sample_ris_data)
    decided_df = execute_rules(agg_df, so_data=sample_so_data)
    
    assert 'R1' in decided_df.columns
    assert 'flags' in decided_df.columns
    # With 50% junior, P1 should trigger R1 (Low Junior)
    p1 = decided_df[decided_df['project_id'] == 'P1'].iloc[0]
    assert p1['R1'] is True

def test_recommendation_engine(sample_ris_data, sample_so_data):
    agg_df = aggregate_by_project(sample_ris_data)
    decided_df = execute_rules(agg_df, so_data=sample_so_data)
    rec_df = generate_recommendations(decided_df, sample_ris_data, sample_so_data)
    
    assert len(rec_df) == 2
    p1_rec = rec_df[rec_df['project_id'] == 'P1'].iloc[0]
    assert 'PYTHON' in p1_rec['training_suggestions'].upper()
    assert 'AWS' in p1_rec['training_suggestions'].upper()

# ── Rule Tests ───────────────────────────────────────────────────────────

def test_r1_low_junior():
    rule = R1LowJuniorRatio()
    # Below target
    data_below = pd.Series({'junior_pct': settings.TARGET_JUNIOR_PCT - 5})
    assert rule.evaluate(data_below) is True
    
    # Above target
    data_above = pd.Series({'junior_pct': settings.TARGET_JUNIOR_PCT + 5})
    assert rule.evaluate(data_above) is False

def test_r2_high_fresher():
    rule = R2HighFresherIntake()
    # Above threshold
    data_above = pd.Series({'junior_pct': settings.R2_HIGH_FRESHER_THRESHOLD_PCT + 5})
    assert rule.evaluate(data_above) is True
    
    # Below threshold
    data_below = pd.Series({'junior_pct': settings.R2_HIGH_FRESHER_THRESHOLD_PCT - 5})
    assert rule.evaluate(data_below) is False

def test_r3_deployment():
    rule = R3FresherDeployment()
    # Gap > 0
    data_gap = pd.Series({'junior_gap': 5})
    assert rule.evaluate(data_gap) is True
    
    # Gap <= 0
    data_no_gap = pd.Series({'junior_gap': -5})
    assert rule.evaluate(data_no_gap) is False
