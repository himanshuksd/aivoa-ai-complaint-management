"""
models.py
---------
Complaint table redesigned to match the actual AIVOA reference demo:
- Fields grouped exactly as the "Log Customer Complaint" form shows them
  (Origin & Customer, Product & Batch, Facility & Material Impact, Defect
  Analysis + AI risk assessment).
- `status` tracks the lifecycle seen in the demo: a complaint starts as a
  DRAFT while the Copilot is still extracting fields from chat/PDF, moves
  to READY once enough fields are filled, and only becomes COMMITTED when
  the user clicks "Commit to QMS Ledger". Only COMMITTED rows are permanent
  QMS records - drafts live in memory (see session_store.py) until then.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    # --- Section 1: Origin & Customer Details ---
    complaint_source = Column(String(100), nullable=True)     # Email / Pharmacy / Phone / Portal
    customer_name = Column(String(255), nullable=True)

    # --- Section 2: Product & Batch Identification ---
    product_name = Column(String(255), nullable=True)
    product_strength = Column(String(100), nullable=True)     # e.g. "500 mg", "IP/BP"
    batch_number = Column(String(100), nullable=True)
    affected_quantity = Column(String(100), nullable=True)    # kept as text: "48 capsules", "25 kg (1 HDPE Drum)"
    manufacturing_date = Column(String(50), nullable=True)
    expiry_date = Column(String(50), nullable=True)

    # --- Section 3: Facility & Material Impact ---
    originating_site_block = Column(String(100), nullable=True)   # e.g. Manufacturing / Packaging / Warehouse
    impacted_npm = Column(String(255), nullable=True)             # Impacted Non-Product Materials

    # --- Section 4: Defect Analysis (raw) ---
    complaint_category = Column(String(150), nullable=True)
    complaint_description = Column(Text, nullable=True)

    # --- Section 4: AI Copilot Risk Assessment ---
    severity = Column(String(50), nullable=True)               # Critical / Major / Minor
    suggested_next_action = Column(Text, nullable=True)
    initial_risk_assessment = Column(Text, nullable=True)

    # --- Lifecycle ---
    status = Column(String(30), default="pending_triage")      # pending_triage | ready_to_commit | committed

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    committed_at = Column(DateTime(timezone=True), nullable=True)
