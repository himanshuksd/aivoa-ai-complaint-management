import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { commitComplaint } from "../store/complaintSlice";

const statusConfig = {
  pending_triage: { label: "Pending Triage", bg: "#fef3c7", color: "#92400e" },
  ready_to_commit: { label: "Ready to Commit", bg: "#d1fae5", color: "#065f46" },
};

export default function ComplaintFormPanel() {
  const dispatch = useDispatch();
  const { sessionId, draft, committing } = useSelector((s) => s.complaints);
  const badge = statusConfig[draft.status] || statusConfig.pending_triage;

  const handleCommit = () => {
    dispatch(commitComplaint(sessionId));
  };

  return (
    <div style={styles.card}>
      <div style={styles.headerRow}>
        <div>
          <h2 style={styles.title}>Log Customer Complaint</h2>
          <p style={styles.subtitle}>API & FDF Quality Assurance Module</p>
        </div>
        <span style={{ ...styles.badge, background: badge.bg, color: badge.color }}>
          ● {badge.label}
        </span>
      </div>

      <Section title="1. Origin & Customer Details">
        <Field label="Complaint Source" value={draft.complaint_source} />
        <Field label="Customer Name" value={draft.customer_name} />
      </Section>

      <Section title="2. Product & Batch Identification">
        <Field label="Product Name" value={draft.product_name} placeholder="Awaiting AI extraction..." />
        <Field label="Product Strength/Grade" value={draft.product_strength} />
        <Field label="Batch / Lot Number" value={draft.batch_number} placeholder="Awaiting AI extraction..." />
        <Field label="Affected Quantity" value={draft.affected_quantity} />
        <Field label="Manufacturing Date" value={draft.manufacturing_date} />
        <Field label="Expiry Date" value={draft.expiry_date} />
      </Section>

      <Section title="3. Facility & Material Impact">
        <Field label="Originating Site Block" value={draft.originating_site_block} placeholder="Awaiting AI classification..." />
        <Field label="Impacted Non-Product Materials (NPM)" value={draft.impacted_npm} placeholder="e.g., Primary packaging..." />
      </Section>

      <Section title="4. Defect Analysis">
        <Field label="Complaint Category" value={draft.complaint_category} />
        <Field
          label="Complaint Description"
          value={draft.complaint_description}
          placeholder="AI will synthesize the complaint into a formal QMS description..."
          multiline
        />
      </Section>

      {draft.severity && (
        <div style={styles.aiBox}>
          <div style={styles.aiBoxTitle}>🛡️ AI Copilot Risk Assessment</div>
          <div style={styles.aiRow}>
            <Field label="Severity (Suggested)" value={draft.severity} compact />
            <Field label="Suggested Next Action" value={draft.suggested_next_action} compact />
          </div>
          <Field label="Initial Risk Assessment" value={draft.initial_risk_assessment} multiline compact />
        </div>
      )}

      <button
        style={{
          ...styles.commitButton,
          opacity: draft.status === "ready_to_commit" ? 1 : 0.5,
          cursor: draft.status === "ready_to_commit" ? "pointer" : "not-allowed",
        }}
        onClick={handleCommit}
        disabled={draft.status !== "ready_to_commit" || committing}
      >
        {committing ? "Committing..." : "Commit to QMS Ledger"}
      </button>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginTop: 20 }}>
      <div style={styles.sectionTitle}>{title}</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 8 }}>{children}</div>
    </div>
  );
}

function Field({ label, value, placeholder = "—", multiline = false, compact = false }) {
  return (
    <div style={{ flex: multiline ? "1 1 100%" : "1 1 45%", minWidth: 180 }}>
      <div style={styles.fieldLabel}>{label}</div>
      <div
        style={{
          ...styles.fieldBox,
          minHeight: multiline ? 60 : "auto",
          color: value ? "#1a1a2e" : "#a0a4ab",
          fontStyle: value ? "normal" : "italic",
          padding: compact ? "8px 10px" : "10px 12px",
        }}
      >
        {value || placeholder}
      </div>
    </div>
  );
}

const styles = {
  card: {
    background: "#fff",
    borderRadius: 12,
    padding: 24,
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
  },
  headerRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-start" },
  title: { margin: 0, fontSize: 20, fontWeight: 700, color: "#1a1a2e" },
  subtitle: { margin: "2px 0 0 0", fontSize: 13, color: "#888" },
  badge: { padding: "6px 12px", borderRadius: 999, fontSize: 12, fontWeight: 600, whiteSpace: "nowrap" },
  sectionTitle: { fontSize: 12, fontWeight: 700, color: "#9ca3af", letterSpacing: 0.5, textTransform: "uppercase" },
  fieldLabel: { fontSize: 13, fontWeight: 500, color: "#555", marginBottom: 4 },
  fieldBox: {
    border: "1px solid #d9dde2",
    borderRadius: 8,
    fontSize: 14,
    background: "#f9fafb",
  },
  aiBox: {
    marginTop: 20,
    background: "#f5f3ff",
    border: "1px solid #ddd6fe",
    borderRadius: 10,
    padding: 16,
  },
  aiBoxTitle: { fontSize: 14, fontWeight: 700, color: "#5b21b6", marginBottom: 10 },
  aiRow: { display: "flex", gap: 12, marginBottom: 10 },
  commitButton: {
    marginTop: 24,
    width: "100%",
    padding: "14px 16px",
    background: "#4f46e5",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontWeight: 700,
    fontSize: 15,
  },
};
