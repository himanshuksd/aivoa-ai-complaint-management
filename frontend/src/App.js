import React from "react";
import ComplaintFormPanel from "./components/ComplaintFormPanel";
import CopilotChat from "./components/CopilotChat";
import ComplaintList from "./components/ComplaintList";

export default function App() {
  return (
    <div style={{ fontFamily: "Inter, sans-serif", padding: "32px", maxWidth: 1200, margin: "0 auto" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, color: "#1a1a2e", marginBottom: 24 }}>
        AIVOA - Customer Complaint Management (Pharma QMS)
      </h1>
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 24, alignItems: "start" }}>
        <ComplaintFormPanel />
        <CopilotChat />
      </div>
      <ComplaintList />
    </div>
  );
}
