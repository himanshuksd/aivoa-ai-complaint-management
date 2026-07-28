"""
schemas.py
----------
Pydantic contracts for the chat-based Copilot API.

Two different "shapes" matter here:
- CopilotDraft: the live, in-progress state shown on the left-hand form
  while the user is chatting (fields may be None if not extracted yet).
- ComplaintResponse: a fully committed QMS record (after "Commit to QMS
  Ledger"), which is what gets persisted and returned by /api/complaints.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ChatMessageIn(BaseModel):
    session_id: str
    message: str


class CopilotDraft(BaseModel):
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None
    affected_quantity: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    originating_site_block: Optional[str] = None
    impacted_npm: Optional[str] = None
    complaint_category: Optional[str] = None
    complaint_description: Optional[str] = None
    severity: Optional[str] = None
    suggested_next_action: Optional[str] = None
    initial_risk_assessment: Optional[str] = None
    status: str = "pending_triage"


class ChatMessageOut(BaseModel):
    session_id: str
    reply: str
    updated_fields: List[str] = []
    draft: CopilotDraft


class CommitRequest(BaseModel):
    session_id: str


class ComplaintResponse(BaseModel):
    id: int
    complaint_source: Optional[str]
    customer_name: Optional[str]
    product_name: Optional[str]
    product_strength: Optional[str]
    batch_number: Optional[str]
    affected_quantity: Optional[str]
    manufacturing_date: Optional[str]
    expiry_date: Optional[str]
    originating_site_block: Optional[str]
    impacted_npm: Optional[str]
    complaint_category: Optional[str]
    complaint_description: Optional[str]
    severity: Optional[str]
    suggested_next_action: Optional[str]
    initial_risk_assessment: Optional[str]
    status: str
    created_at: datetime
    committed_at: Optional[datetime]

    class Config:
        from_attributes = True
