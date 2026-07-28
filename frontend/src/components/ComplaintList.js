import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { loadComplaints } from "../store/complaintSlice";

export default function ComplaintList() {
  const dispatch = useDispatch();
  const { committedList } = useSelector((s) => s.complaints);

  useEffect(() => {
    dispatch(loadComplaints());
  }, [dispatch]);

  return (
    <div style={styles.card}>
      <h2 style={styles.heading}>QMS Complaint Ledger</h2>
      {committedList.length === 0 && (
        <p style={{ color: "#888", fontSize: 14 }}>No complaints committed yet.</p>
      )}
      {committedList.length > 0 && (
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>ID</th>
              <th style={styles.th}>Customer</th>
              <th style={styles.th}>Product</th>
              <th style={styles.th}>Category</th>
              <th style={styles.th}>Severity</th>
              <th style={styles.th}>Committed At</th>
            </tr>
          </thead>
          <tbody>
            {committedList.map((c) => (
              <tr key={c.id}>
                <td style={styles.td}>{c.id}</td>
                <td style={styles.td}>{c.customer_name}</td>
                <td style={styles.td}>{c.product_name}</td>
                <td style={styles.td}>{c.complaint_category}</td>
                <td style={styles.td}>{c.severity}</td>
                <td style={styles.td}>{c.committed_at ? new Date(c.committed_at).toLocaleString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const styles = {
  card: {
    background: "#fff",
    borderRadius: 12,
    padding: 24,
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
    marginTop: 24,
  },
  heading: { margin: "0 0 12px 0", fontSize: 18, fontWeight: 600, color: "#1a1a2e" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 14 },
  th: { textAlign: "left", padding: 8, borderBottom: "2px solid #eee", color: "#888" },
  td: { padding: 8, borderBottom: "1px solid #f0f0f0" },
};
