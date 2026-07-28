# AIVOA - AI-Powered Customer Complaint Management System (v2)

Pharmaceutical (API/FDF manufacturing) QMS Customer Complaint module with a
**conversational AI Copilot**: paste a customer email or upload a PDF, the
Copilot extracts fields into the "Log Customer Complaint" form live, you
can correct individual fields via chat, and once required fields are
present you commit the record to the QMS ledger.

This version was rebuilt after reviewing the actual AIVOA reference demo
video, replacing an earlier single-form-submit v1 design.

## Architecture

```
React (Redux Toolkit)        FastAPI                  LangGraph workflow           Groq LLMs
  CopilotChat          --->  POST /api/copilot/message  extract_and_merge   --->  gemma2-9b-it (extraction)
  ComplaintFormPanel    <--- POST /api/copilot/upload  -> assess_risk (cond.) --> llama-3.3-70b-versatile (risk/CAPA)
  ComplaintList         <--- POST /api/complaints/commit -> compose_reply
                              GET  /api/complaints
                                    |
                          session_store.py (in-memory draft)
                                    |
                          SQLAlchemy (SQLite / Postgres) - only on commit
```

### Why this shape (matches the reference demo)
- **Draft vs committed record are different things.** While chatting, the
  in-progress complaint lives only in `session_store.py` (in-memory,
  keyed by a per-tab `session_id`). Nothing touches the database until the
  user clicks **"Commit to QMS Ledger"** (`POST /api/complaints/commit`),
  which is the moment a permanent QMS record is created. This mirrors the
  demo's "Pending Triage" -> "Ready to Commit" -> commit lifecycle.
- **Incremental extraction, not one-shot.** Every chat turn
  (`extract_and_merge_node` in `ai_workflow.py`) sees the *current* draft
  plus the *new* message, and the LLM is instructed to return only the
  fields it found evidence for in that message. We merge those onto the
  draft server-side. This is why a follow-up like "ah sorry the batch
  number is X" updates only that field instead of re-extracting (and
  possibly corrupting) everything else - directly matching the demo.
- **Conditional risk assessment.** `should_assess_risk` is a LangGraph
  conditional edge: risk assessment only fires once we have a product name
  and a description of the issue, not on every single turn.
- **PDF upload uses plain text extraction** (`pdf_utils.py`, via `pypdf`) -
  no OCR, per the assignment's explicit note that production-grade OCR
  isn't required. Extracted text is fed into the same `extract_and_merge`
  node as typed chat messages, so PDF and typed-text paths share one code
  path.
- **Two models, different jobs.** `gemma2-9b-it` handles field extraction
  (fast, structured). `llama-3.3-70b-versatile` handles risk assessment
  (needs more reasoning to weigh severity and suggest next actions).

## Setup

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # paste your free Groq API key from console.groq.com/keys
uvicorn main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` for interactive API docs.

### Frontend
```bash
cd frontend
npm install
npm start
```
Visit `http://localhost:3000`.

## API

| Method | Path                        | Purpose                                                         |
|--------|-----------------------------|------------------------------------------------------------------|
| POST   | `/api/copilot/message`      | Send a chat message (paste complaint text or a correction)      |
| POST   | `/api/copilot/upload`       | Upload a PDF; extracted text is run through the same extraction |
| POST   | `/api/complaints/commit`    | Commit the current session's draft to the permanent QMS ledger  |
| GET    | `/api/complaints`           | List committed complaints (ledger view)                          |
| GET    | `/api/complaints/{id}`      | Fetch a single committed complaint                                |

## What to demo / explain
1. Paste a raw complaint email into the Copilot chat, or upload a PDF.
2. Watch the "Log Customer Complaint" form populate live from the reply.
3. Send a correction message (e.g. "actually the batch number is X") and
   show that only that field changes in the form - explain why, pointing
   at `extract_and_merge_node` and the merge-not-overwrite logic.
4. Once status flips to "Ready to Commit", click **Commit to QMS Ledger**
   and show the row appear in the Complaint Ledger table below, backed by
   the DB.
5. Walk through `main.py` -> `ai_workflow.run_copilot_turn()` -> the graph
   nodes firing in order (`extract_and_merge` -> conditional `assess_risk`
   -> `compose_reply`), and show the Groq API calls.

## Known limitations (be ready to name these, don't hide them)
- Session drafts are in-memory only (`session_store.py`) - lost on server
  restart, and won't work across multiple backend processes. A real
  deployment would use Redis or a `draft_complaints` DB table with a TTL.
- No duplicate complaint detection implemented.
- No authentication - anyone can commit to the ledger.
- PDF extraction is plain text only, no OCR for scanned/image-based PDFs.
