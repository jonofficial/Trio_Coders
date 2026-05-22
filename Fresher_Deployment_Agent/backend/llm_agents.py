import json
import os
import pandas as pd
from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from backend.logger import logger
from dotenv import load_dotenv
from pathlib import Path

# Resolve .env relative to this file (backend/.env) regardless of CWD
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# ── Sanitization ────────────────────────────────────────────────────────────

def sanitize_project_data(project_row: pd.Series, ris_skills: set, so_skills: set) -> Dict[str, Any]:
    """
    Strict data sanitization before LLM calls.
    Ensures no PII or raw DataFrames are passed to the LLM.
    Returns only high-level aggregates and text features.
    """
    return {
        "project_name": str(project_row.get("project_name", "UNKNOWN")),
        "junior_gap_percentage": round(float(project_row.get("junior_gap", 0)), 2),
        "current_junior_percentage": round(float(project_row.get("junior_pct", 0)), 2),
        "team_size": int(project_row.get("total_headcount", 0)),
        "current_team_skills": list(ris_skills),
        "demanded_skills": list(so_skills)
    }


# ── R3 Agent ─────────────────────────────────────────────────────────────────

class DeploymentSuitability(BaseModel):
    suitable_for_fresher: bool = Field(description="Whether the project is suitable for a fresher")
    skill_overlap_score: float = Field(description="Score between 0.0 and 1.0 for skill overlap")
    role_match_score: float = Field(description="Score between 0.0 and 1.0 for role match")
    reasoning: str = Field(description="Brief explanation of the evaluation")

def analyze_deployment_opportunity(sanitized_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    R3 LLM Agent: Evaluates role/skill suitability for fresher deployment.
    Uses Groq to analyze skill compatibility and determine an overlap score.
    """
    if not os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY") == "your_api_key_here":
        logger.warning("GROQ_API_KEY not set. Using fallback R3 logic.")
        return fallback_r3_logic(sanitized_data)

    try:
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)
        structured_llm = llm.with_structured_output(DeploymentSuitability)

        prompt = PromptTemplate.from_template(
            """
            You are an expert IT resource management AI. Evaluate the following project for entry-level (fresher) deployment suitability.

            Project Data:
            {data}

            Analyze the overlap between "current_team_skills" (what the team currently has) and "demanded_skills" (what is needed).
            Determine if the demanded skills are suitable for an entry-level employee to learn.
            Also evaluate the role match suitability based on the skills context.
            """
        )

        chain = prompt | structured_llm

        logger.info(f"AUDIT LOG - R3 LLM Input for {sanitized_data.get('project_name')}: {json.dumps(sanitized_data)}")

        result = chain.invoke({"data": json.dumps(sanitized_data, indent=2)})
        output_dict = result.model_dump()

        logger.info(f"AUDIT LOG - R3 LLM Output: {json.dumps(output_dict)}")
        return output_dict

    except Exception as e:
        logger.error(f"R3 LLM failed for {sanitized_data.get('project_name')}: {e}")
        return fallback_r3_logic(sanitized_data)

def fallback_r3_logic(data: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback rule-based logic if LLM fails or is unavailable."""
    overlap = len(set(data["current_team_skills"]).intersection(set(data["demanded_skills"])))
    score = min(1.0, overlap * 0.2)
    return {
        "suitable_for_fresher": data["junior_gap_percentage"] > 0,
        "skill_overlap_score": score,
        "role_match_score": 0.5,
        "reasoning": "Fallback deterministic logic used due to missing API key or LLM error."
    }


# ── R4 Agent ─────────────────────────────────────────────────────────────────

class TrainingTrack(BaseModel):
    training_required: bool = Field(description="Whether specific training is required based on the skill gap")
    track_name: str = Field(description="The logical name of the training track (e.g. Fullstack Web Development)")
    priority: str = Field(description="High/Medium/Low priority based on the number of open roles")
    skills_covered: List[str] = Field(description="The specific skills from the SO data clustered here")
    curriculum_summary: str = Field(description="A 1-sentence description of what a fresher will learn in this track")
    reasoning: str = Field(description="Why this training is suggested")

def generate_training_suggestions(sanitized_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    R4 LLM Agent: Generates training themes based on skill gaps.
    Uses strict JSON schema enforcement via Pydantic structured output.
    """
    if not os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY") == "your_api_key_here":
        logger.warning("GROQ_API_KEY not set. Using fallback R4 logic.")
        return fallback_r4_logic(sanitized_data)

    try:
        # Use a model that supports structured outputs well
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)
        structured_llm = llm.with_structured_output(TrainingTrack)

        prompt = PromptTemplate.from_template(
            """
            You are a Technical Training Architect. Look at the demanded skills and current team skills below.
            Instead of just listing them, group them into a logical **Training Track** using a Skill Taxonomy.
            (e.g., Backend, Frontend, DevOps, Data Science, Enterprise Java, etc.)
            
            Project Data:
            {data}

            If "demanded_skills" is empty, suggest "General Fresher Onboarding".
            Otherwise, create a structured curriculum track based on the semantic clustering of these skills.
            Provide a track name, priority, a list of specific skills covered in this track, and a 1-sentence curriculum summary.
            """
        )

        chain = prompt | structured_llm

        logger.info(f"AUDIT LOG - R4 LLM Input for {sanitized_data.get('project_name')}: {json.dumps(sanitized_data)}")

        result: TrainingTrack = chain.invoke({"data": json.dumps(sanitized_data, indent=2)})
        output_dict = result.model_dump()

        logger.info(f"AUDIT LOG - R4 LLM Output: {json.dumps(output_dict)}")
        return output_dict

    except Exception as e:
        logger.error(f"R4 LLM failed for {sanitized_data.get('project_name')}: {e}")
        return fallback_r4_logic(sanitized_data)

def fallback_r4_logic(data: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback rule-based logic if LLM fails or is unavailable."""
    all_skills = set(data["current_team_skills"]).union(set(data["demanded_skills"]))
    if all_skills:
        track = "Foundational Technical Training"
        summary = f"Core fundamentals focusing on existing and demanded technologies."
        skills = list(all_skills)
    else:
        track = "General Fresher Onboarding"
        summary = "Standard project orientation and onboarding."
        skills = []

    return {
        "training_required": True,
        "track_name": track,
        "priority": "Medium",
        "skills_covered": skills,
        "curriculum_summary": summary,
        "reasoning": "Fallback deterministic logic used."
    }
