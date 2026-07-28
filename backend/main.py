"""
main.py
-------
FastAPI app for the AIVOA Copilot complaint workflow.

Three-endpoint flow, matching the reference demo:

  1. POST /api/copilot/message  - send a chat message (pasted email/text or
     a correction). Runs one LangGraph turn, merges extracted fields into
     the session's draft, returns the Copilot's reply + the updated draft
     (this is what repopulates the "Log Customer Complaint" form live).

  2. POST /api/copilot/upload   - same as above, but the "message" is text
     extracted from an uploaded PDF instead of typed text.

  3. POST /api/complaints/commit - "Commit to QMS Ledger". Takes the
     session's current draft, writes it as a permanent Complaint row with
     status=committed, and clears the in-memory session.

  GET /api/complaints            - list committed complaints (QMS ledger view)
  GET /api/complaints/{id}       - fetch one committed complaint
"""
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone

import models
import schemas
import session_store
from database import engine, get_db
from ai_workflow import run_copilot_turn, DRAFT_FIELDS, RISK_FIELDS
from pdf_utils import extract_text_from_pdf

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AIVOA Customer Complaint Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


def _draft_to_response(session_id: str, reply: str, updated_fields: list, draft: dict) -> schemas.ChatMessageOut:
    status = session_store.compute_status(draft)
    return schemas.ChatMessageOut(
        session_id=session_id,
        reply=reply,
        updated_fields=updated_fields,
        draft=schemas.CopilotDraft(**{k: draft.get(k) for k in DRAFT_FIELDS + RISK_FIELDS}, status=status),
    )


@app.post("/api/copilot/message", response_model=schemas.ChatMessageOut)
def copilot_message(payload: schemas.ChatMessageIn):
    current_draft = session_store.get_draft(payload.session_id)
    result = run_copilot_turn(current_draft, payload.message)
    session_store.save_draft(payload.session_id, result["draft"])
    return _draft_to_response(payload.session_id, result["reply"], result["updated_fields"], result["draft"])


@app.post("/api/copilot/upload", response_model=schemas.ChatMessageOut)
async def copilot_upload(session_id: str = Form(...), file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported in this MVP.")

    file_bytes = await file.read()
    extracted_text = extract_text_from_pdf(file_bytes)
    if not extracted_text:
        raise HTTPException(status_code=422, detail="Could not extract any text from this PDF.")

    current_draft = session_store.get_draft(session_id)
    result = run_copilot_turn(current_draft, extracted_text)
    session_store.save_draft(session_id, result["draft"])
    return _draft_to_response(session_id, result["reply"], result["updated_fields"], result["draft"])


@app.post("/api/complaints/commit", response_model=schemas.ComplaintResponse)
def commit_complaint(payload: schemas.CommitRequest, db: Session = Depends(get_db)):
    draft = session_store.get_draft(payload.session_id)
    if not draft:
        raise HTTPException(status_code=404, detail="No active draft found for this session.")

    status = session_store.compute_status(draft)
    if status != "ready_to_commit":
        raise HTTPException(
            status_code=400,
            detail="Draft is missing required fields (product name, batch number, complaint description).",
        )

    complaint = models.Complaint(
        **{k: draft.get(k) for k in DRAFT_FIELDS + RISK_FIELDS},
        status="committed",
        committed_at=datetime.now(timezone.utc),
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    session_store.clear_draft(payload.session_id)
    return complaint


@app.get("/api/complaints", response_model=list[schemas.ComplaintResponse])
def list_complaints(db: Session = Depends(get_db)):
    return db.query(models.Complaint).order_by(desc(models.Complaint.created_at)).all()


@app.get("/api/complaints/{complaint_id}", response_model=schemas.ComplaintResponse)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint
