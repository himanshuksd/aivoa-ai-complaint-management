import React, { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendMessage, uploadFile } from "../store/complaintSlice";

export default function CopilotChat() {
  const dispatch = useDispatch();
  const { sessionId, messages, chatting } = useSelector((s) => s.complaints);
  const [input, setInput] = useState("");
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatting]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || chatting) return;
    dispatch(sendMessage({ sessionId, message: trimmed }));
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    dispatch(uploadFile({ sessionId, file }));
    e.target.value = ""; // allow re-uploading the same file name later
  };

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <span style={{ fontSize: 20 }}>🧪</span>
        <div>
          <div style={styles.headerTitle}>AIVOA Copilot</div>
          <div style={styles.headerSubtitle}>Drop complaint files or paste text below.</div>
        </div>
      </div>

      <div style={styles.messagesArea}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              ...styles.messageRow,
              justifyContent: m.sender === "user" ? "flex-end" : "flex-start",
            }}
          >
            <div
              style={{
                ...styles.bubble,
                ...(m.sender === "user" ? styles.userBubble : styles.aiBubble),
              }}
            >
              {m.text}
            </div>
          </div>
        ))}
        {chatting && (
          <div style={{ ...styles.messageRow, justifyContent: "flex-start" }}>
            <div style={{ ...styles.bubble, ...styles.aiBubble }}>●●●</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={styles.inputRow}>
        <button style={styles.attachButton} onClick={() => fileInputRef.current?.click()} title="Upload PDF">
          📎
        </button>
        <input
          type="file"
          accept="application/pdf"
          ref={fileInputRef}
          style={{ display: "none" }}
          onChange={handleFileChange}
        />
        <input
          style={styles.textInput}
          placeholder="Type a message or paste a complaint..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button style={styles.sendButton} onClick={handleSend} disabled={chatting}>
          ✓
        </button>
      </div>
      <div style={styles.poweredBy}>POWERED BY LANGGRAPH</div>
    </div>
  );
}

const styles = {
  card: {
    background: "#fff",
    borderRadius: 12,
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
    display: "flex",
    flexDirection: "column",
    height: "80vh",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "16px 20px",
    borderBottom: "1px solid #eee",
  },
  headerTitle: { fontSize: 16, fontWeight: 700, color: "#1a1a2e" },
  headerSubtitle: { fontSize: 12, color: "#888" },
  messagesArea: { flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 10 },
  messageRow: { display: "flex" },
  bubble: { maxWidth: "80%", padding: "10px 14px", borderRadius: 12, fontSize: 14, lineHeight: 1.4 },
  userBubble: { background: "#4f46e5", color: "#fff", borderBottomRightRadius: 4 },
  aiBubble: { background: "#f3f4f6", color: "#1a1a2e", borderBottomLeftRadius: 4 },
  inputRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: 12,
    borderTop: "1px solid #eee",
  },
  attachButton: {
    background: "none",
    border: "none",
    fontSize: 18,
    cursor: "pointer",
    padding: 6,
  },
  textInput: {
    flex: 1,
    padding: "10px 14px",
    borderRadius: 20,
    border: "1px solid #d9dde2",
    fontFamily: "Inter, sans-serif",
    fontSize: 14,
  },
  sendButton: {
    background: "#4f46e5",
    color: "#fff",
    border: "none",
    borderRadius: "50%",
    width: 36,
    height: 36,
    cursor: "pointer",
    fontSize: 14,
  },
  poweredBy: {
    textAlign: "center",
    fontSize: 10,
    color: "#bbb",
    letterSpacing: 1,
    padding: "6px 0 10px 0",
  },
};
