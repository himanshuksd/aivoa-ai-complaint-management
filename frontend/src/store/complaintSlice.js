import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import {
  sendCopilotMessage,
  uploadCopilotFile,
  commitComplaint as commitComplaintApi,
  fetchComplaints,
} from "../api/api";

// A fresh session id per browser tab/page-load - the backend keeps the
// in-progress draft keyed by this on session_store.py. Real auth/user
// identity would replace this in production.
const makeSessionId = () =>
  "session-" + Math.random().toString(36).slice(2) + Date.now();

const emptyDraft = {
  complaint_source: null,
  customer_name: null,
  product_name: null,
  product_strength: null,
  batch_number: null,
  affected_quantity: null,
  manufacturing_date: null,
  expiry_date: null,
  originating_site_block: null,
  impacted_npm: null,
  complaint_category: null,
  complaint_description: null,
  severity: null,
  suggested_next_action: null,
  initial_risk_assessment: null,
  status: "pending_triage",
};

// Sends a typed chat message to the Copilot. The response contains the
// AI's reply AND the full updated draft, which is why one thunk can drive
// both the chat panel and the "Log Customer Complaint" form on the left.
export const sendMessage = createAsyncThunk(
  "complaints/sendMessage",
  async ({ sessionId, message }, { rejectWithValue }) => {
    try {
      const res = await sendCopilotMessage(sessionId, message);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Message failed");
    }
  }
);

export const uploadFile = createAsyncThunk(
  "complaints/uploadFile",
  async ({ sessionId, file }, { rejectWithValue }) => {
    try {
      const res = await uploadCopilotFile(sessionId, file);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Upload failed");
    }
  }
);

export const commitComplaint = createAsyncThunk(
  "complaints/commit",
  async (sessionId, { rejectWithValue }) => {
    try {
      const res = await commitComplaintApi(sessionId);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Commit failed");
    }
  }
);

export const loadComplaints = createAsyncThunk(
  "complaints/loadAll",
  async (_, { rejectWithValue }) => {
    try {
      const res = await fetchComplaints();
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Failed to load complaints");
    }
  }
);

const complaintSlice = createSlice({
  name: "complaints",
  initialState: {
    sessionId: makeSessionId(),
    draft: emptyDraft,
    messages: [
      {
        sender: "ai",
        text: "Ready to process new complaints. You can paste the raw email from the customer, or upload a PDF of the complaint report. I will extract the data and run the initial risk assessment.",
      },
    ],
    chatting: false,
    committing: false,
    committedList: [],
    error: null,
  },
  reducers: {
    startNewSession(state) {
      state.sessionId = makeSessionId();
      state.draft = emptyDraft;
      state.messages = [
        {
          sender: "ai",
          text: "Ready to process new complaints. You can paste the raw email from the customer, or upload a PDF of the complaint report. I will extract the data and run the initial risk assessment.",
        },
      ];
    },
  },
  extraReducers: (builder) => {
    builder
      // --- sendMessage ---
      .addCase(sendMessage.pending, (state, action) => {
        state.chatting = true;
        state.error = null;
        state.messages.push({ sender: "user", text: action.meta.arg.message });
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.chatting = false;
        state.draft = action.payload.draft;
        state.messages.push({ sender: "ai", text: action.payload.reply });
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.chatting = false;
        state.error = action.payload;
      })
      // --- uploadFile ---
      .addCase(uploadFile.pending, (state, action) => {
        state.chatting = true;
        state.error = null;
        state.messages.push({
          sender: "user",
          text: `📄 ${action.meta.arg.file.name}`,
          isFile: true,
        });
      })
      .addCase(uploadFile.fulfilled, (state, action) => {
        state.chatting = false;
        state.draft = action.payload.draft;
        state.messages.push({ sender: "ai", text: action.payload.reply });
      })
      .addCase(uploadFile.rejected, (state, action) => {
        state.chatting = false;
        state.error = action.payload;
      })
      // --- commit ---
      .addCase(commitComplaint.pending, (state) => {
        state.committing = true;
        state.error = null;
      })
      .addCase(commitComplaint.fulfilled, (state, action) => {
        state.committing = false;
        state.committedList.unshift(action.payload);
        // Start a fresh session/draft for the next complaint, mirroring
        // the demo resetting to "Pending Triage" after a commit.
        state.sessionId = makeSessionId();
        state.draft = emptyDraft;
        state.messages = [
          {
            sender: "ai",
            text: "Complaint committed to the QMS ledger. Ready to process a new complaint whenever you are.",
          },
        ];
      })
      .addCase(commitComplaint.rejected, (state, action) => {
        state.committing = false;
        state.error = action.payload;
      })
      // --- loadComplaints ---
      .addCase(loadComplaints.fulfilled, (state, action) => {
        state.committedList = action.payload;
      });
  },
});

export const { startNewSession } = complaintSlice.actions;
export default complaintSlice.reducer;
