import axios from "axios";

// FastAPI backend runs on :8000 by default (see backend/main.py + uvicorn command).
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000/api",
});

export const sendCopilotMessage = (sessionId, message) =>
  api.post("/copilot/message", { session_id: sessionId, message });

export const uploadCopilotFile = (sessionId, file) => {
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("file", file);
  return api.post("/copilot/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const commitComplaint = (sessionId) =>
  api.post("/complaints/commit", { session_id: sessionId });

export const fetchComplaints = () => api.get("/complaints");

export default api;
