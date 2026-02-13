from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
import json
import os
from dotenv import load_dotenv
from services.skill_gap_graph import clean_json_output

load_dotenv()

class ScreeningState(TypedDict):
    resume_text: str
    jd_text: str
    decision: Optional[dict]
    score: Optional[dict]
    config: Optional[dict]

def get_llm(config: Optional[dict]):
    """Helper to initialize LLM from config or environment."""
    if config and config.get("api_key"):
        return ChatOpenAI(
            model=config.get("model", "gpt-4o-mini"),
            temperature=config.get("temperature", 0),
            api_key=config.get("api_key"),
            base_url=config.get("base_url", "https://openrouter.ai/api/v1")
        )
    # Fallback to .env
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPEN_ROUTER_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

def screening_agent(state: ScreeningState):
    llm = get_llm(state.get("config"))
    prompt = PromptTemplate(
        input_variables=["resume", "jd"],
        template="""
You are an expert AI recruiter.

Job Description:
{jd}

Candidate Resume:
{resume}

TASK:
1. Evaluate if the candidate is a match for the job (Selected/Rejected).
2. Provide a score (0-100) based on skills, experience, and relevance.
3. Provide a brief reason for the decision.

Return ONLY valid JSON:
{{
  "decision": {{
    "selected": true,
    "reason": "Strong match with AWS and Python experience."
  }},
  "score": {{
      "overall": 85
  }}
}}
"""
    )
    
    try:
        response = llm.invoke(prompt.format(resume=state["resume_text"], jd=state["jd_text"]))
        clean_content = clean_json_output(response.content)
        result = json.loads(clean_content)
        
        return {
            "decision": result.get("decision", {"selected": False, "reason": "Error parsing decision"}),
            "score": result.get("score", {"overall": 0})
        }
    except Exception as e:
        return {
            "decision": {"selected": False, "reason": f"Error in screening: {str(e)}"},
            "score": {"overall": 0}
        }

def build_screening_graph():
    graph = StateGraph(ScreeningState)
    graph.add_node("screen", screening_agent)
    graph.set_entry_point("screen")
    graph.add_edge("screen", END)
    return graph.compile()
