"""
ai_workflow.py
--------------
The AIVOA Copilot's brain. Redesigned (v2) to match the actual reference
demo: this is a MULTI-TURN, INCREMENTAL extraction workflow, not a
one-shot pipeline.

Why incremental, not one-shot (like v1 was):
In the demo, a user pastes a complaint, the Copilot extracts what it can,
and then the user sends a FOLLOW-UP correction ("ah sorry the batch number
is X and affected quantity is Y") - and only those two fields update,
everything else the Copilot already extracted stays untouched. That means
every turn needs to see the CURRENT DRAFT plus the NEW message, and merge
rather than overwrite.

Graph shape (runs once per chat turn):

    extract_and_merge -> assess_risk (conditional) -> compose_reply -> END

- extract_and_merge: LLM sees the existing draft (as JSON) + the new
  message, and returns ONLY the fields it found/changed this turn. We
  merge that onto the draft server-side (not by overwriting the whole
  draft) so nothing already-correct gets clobbered by omission.
- assess_risk: only runs once we have enough signal (a product name AND
  a description of the issue) - this is a conditional edge, unlike v1
  which ran risk assessment unconditionally after every complaint.
- compose_reply: drafts the natural-language chat reply, explicitly told
  which fields changed this turn, so it can say things like "I've updated
  the Batch/Lot Number to X and Affected Quantity to Y" - matching the
  demo's Copilot tone.

Session/draft state lives in `session_store.py` (simple in-memory dict for
this MVP - see that file's docstring for the production note on swapping
to Redis/DB-backed sessions).
"""
import os
import json
import re
from typing import TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=GROQ_API_KEY, temperature=0)
llm_reasoning = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY, temperature=0.2)

DRAFT_FIELDS = [
    "complaint_source", "customer_name", "product_name", "product_strength",
    "batch_number", "affected_quantity", "manufacturing_date", "expiry_date",
    "originating_site_block", "impacted_npm", "complaint_category",
    "complaint_description",
]
RISK_FIELDS = ["severity", "suggested_next_action", "initial_risk_assessment"]


class CopilotState(TypedDict, total=False):
    draft: dict            # current accumulated field values
    incoming_text: str     # this turn's user message (typed or PDF-extracted)
    updated_fields: list    # which draft keys changed this turn (for the reply + UI)
    reply: str


def _ask_json(model, prompt: str) -> dict:
    """Same defensive JSON parsing as v1: strip markdown fences, grab the
    first {...} block, fail closed to {} rather than crashing the graph."""
    response = model.invoke(prompt)
    text = response.content.strip()
    text = re.sub(r"^```json|^```|```$", "", text, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def extract_and_merge_node(state: CopilotState) -> dict:
    draft = state.get("draft", {})
    prompt = f"""You are the AIVOA Copilot, an AI assistant inside a pharmaceutical
Quality Management System that helps QA staff log customer complaints.

Current draft of the complaint form (fields already known - JSON, may be
partially empty):
{json.dumps({k: draft.get(k) for k in DRAFT_FIELDS}, indent=2)}

New message from the QA user (may be a pasted customer email, extracted
PDF text, or a short correction like "the batch number is actually X"):
\"\"\"{state['incoming_text']}\"\"\"

Extract or correct ONLY the fields you have clear evidence for in this new
message. If a field isn't mentioned in the new message, DO NOT include it
in your response - leave it out entirely so the existing value is kept.
Valid field keys: {DRAFT_FIELDS}

complaint_source should be one of: Email, Pharmacy, Phone, Portal, Distributor.
originating_site_block should be one of: Manufacturing, Packaging, Warehouse, QC Lab.

Respond ONLY with a JSON object of the fields you are setting/updating, e.g.:
{{"batch_number": "BMX240602", "affected_quantity": "48 capsules"}}"""

    extracted = _ask_json(llm, prompt)
    changes = {k: v for k, v in extracted.items() if k in DRAFT_FIELDS and v}

    merged_draft = {**draft, **changes}
    return {"draft": merged_draft, "updated_fields": list(changes.keys())}


def should_assess_risk(state: CopilotState) -> str:
    """Conditional edge: only run risk assessment once we have a product
    name and some description of the actual issue to reason about."""
    draft = state.get("draft", {})
    has_signal = bool(draft.get("product_name")) and bool(
        draft.get("complaint_description") or draft.get("complaint_category")
    )
    return "assess_risk" if has_signal else "compose_reply"


def assess_risk_node(state: CopilotState) -> dict:
    draft = state["draft"]
    prompt = f"""You are a senior QA specialist at a pharmaceutical manufacturing
site (API/FDF). Based on this complaint draft, provide a preliminary risk
assessment for a human QA reviewer to validate - this is a DRAFT suggestion,
not a final decision.

Product: {draft.get('product_name')}
Category: {draft.get('complaint_category')}
Description: {draft.get('complaint_description')}
Affected quantity: {draft.get('affected_quantity')}

Respond ONLY with JSON:
{{
  "complaint_category": "<short defect category, e.g. 'Foreign Matter Contamination', 'Product Defect - Discoloration'>",
  "severity": "Critical|Major|Minor",
  "suggested_next_action": "<short actionable next step, e.g. 'Laboratory investigation & manufacturing record review'>",
  "initial_risk_assessment": "<2-3 sentence preliminary risk assessment>"
}}"""
    result = _ask_json(llm_reasoning, prompt)
    changes = {k: v for k, v in result.items() if k in DRAFT_FIELDS + RISK_FIELDS and v}
    merged_draft = {**draft, **changes}

    prior_updates = state.get("updated_fields", [])
    return {"draft": merged_draft, "updated_fields": prior_updates + list(changes.keys())}


def compose_reply_node(state: CopilotState) -> dict:
    updated = state.get("updated_fields", [])
    draft = state["draft"]

    if not updated:
        return {"reply": "I didn't find any new information to update in that message. Could you clarify?"}

    prompt = f"""You are the AIVOA Copilot chat assistant in a pharmaceutical QMS.
You just updated these fields in the complaint form: {updated}
Current values of those fields: {json.dumps({k: draft.get(k) for k in updated})}

Write ONE short, natural confirmation message (2-3 sentences max) to the QA
user, similar in tone to: "Complaint parsed successfully. I've extracted
the product details, mapped the batch information, and generated an
initial risk assessment." or "Got it. I've updated the Batch/Lot Number to
X and the Affected Quantity to Y in the form."

Respond ONLY with JSON: {{"reply": "<your message>"}}"""
    result = _ask_json(llm, prompt)
    reply = result.get("reply") or f"Updated: {', '.join(updated)}."
    return {"reply": reply}


def build_graph():
    graph = StateGraph(CopilotState)
    graph.add_node("extract_and_merge", extract_and_merge_node)
    graph.add_node("assess_risk", assess_risk_node)
    graph.add_node("compose_reply", compose_reply_node)

    graph.set_entry_point("extract_and_merge")
    graph.add_conditional_edges(
        "extract_and_merge",
        should_assess_risk,
        {"assess_risk": "assess_risk", "compose_reply": "compose_reply"},
    )
    graph.add_edge("assess_risk", "compose_reply")
    graph.add_edge("compose_reply", END)

    return graph.compile()


copilot_workflow = build_graph()


def run_copilot_turn(current_draft: dict, incoming_text: str) -> dict:
    """Entry point called by the FastAPI route for every chat message."""
    initial_state: CopilotState = {"draft": current_draft, "incoming_text": incoming_text}
    final_state = copilot_workflow.invoke(initial_state)
    return {
        "draft": final_state["draft"],
        "updated_fields": final_state.get("updated_fields", []),
        "reply": final_state.get("reply", ""),
    }
