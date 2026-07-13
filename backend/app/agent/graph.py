"""LangGraph state machine graph workflow compiling the agentic reasoning loop."""

import logging
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.nodes.chain import forward_chain_node
from app.agent.nodes.compose import compose_response_node
from app.agent.nodes.evaluate import evaluate_rules_node
from app.agent.nodes.extract import extract_profile_node
from app.agent.nodes.retrieve import retrieve_candidates_node

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Shared state container dict for the reasoning graph flow."""

    user_query: str
    preferred_language: str
    extracted_profile: Dict[str, Any]
    candidate_schemes: List[Dict[str, Any]]
    eligible_schemes: List[Dict[str, Any]]
    suggested_schemes: List[Dict[str, Any]]
    reply_text: str


# 1. Initialize Graph State Workflow
workflow = StateGraph(AgentState)

# 2. Add Reasoning Nodes
workflow.add_node("extract_profile", extract_profile_node)
workflow.add_node("retrieve_candidates", retrieve_candidates_node)
workflow.add_node("evaluate_rules", evaluate_rules_node)
workflow.add_node("forward_chain", forward_chain_node)
workflow.add_node("compose_response", compose_response_node)

# 3. Add Sequential Edges
workflow.add_edge(START, "extract_profile")
workflow.add_edge("extract_profile", "retrieve_candidates")
workflow.add_edge("retrieve_candidates", "evaluate_rules")
workflow.add_edge("evaluate_rules", "forward_chain")
workflow.add_edge("forward_chain", "compose_response")
workflow.add_edge("compose_response", END)

# 4. Compile State Machine
agent_app = workflow.compile()


async def run_agent(
    user_query: str,
    extracted_profile: Optional[Dict[str, Any]] = None,
    language: str = "hi",
) -> Dict[str, Any]:
    """Helper entrypoint to invoke the compiled LangGraph agent.

    Args:
        user_query: Latest user query query text.
        extracted_profile: Initial extracted demographic profile parameters.
        language: Interaction language code preference.

    Returns:
        Final resulting state dictionary containing composed reply_text.
    """
    initial_state: AgentState = {
        "user_query": user_query,
        "preferred_language": language,
        "extracted_profile": extracted_profile or {},
        "candidate_schemes": [],
        "eligible_schemes": [],
        "suggested_schemes": [],
        "reply_text": "",
    }
    logger.info(f"[LANGGRAPH ROUTER] Invoking agent for query: '{user_query}'")
    result = await agent_app.ainvoke(initial_state)
    return dict(result)
