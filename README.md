# 📄 DocuChat AI — Full-Stack Document RAG Platform

A production-ready, full-stack AI application built with a **React frontend** and a **FastAPI backend**. It implements **Retrieval-Augmented Generation (RAG)** to let users upload multi-page PDF documents, ask questions, get instant summaries, and inspect verified source citations with exact page attribution.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   React Frontend                       │
│    (Vite, Modern CSS, Lucide Icons, Clean UI)          │
│   • Drag & Drop PDF Uploader                           │
│   • Real-time Document Metric Pills                    │
│   • Interactive Chat Feed with Citation Drawers        │
│   • 1-Click Action Chips (Summaries & Key Takeaways)   │
└──────────────────────────▲─────────────────────────────┘
                           │  HTTP / JSON (REST API)
                           │  CORS-enabled
┌──────────────────────────▼─────────────────────────────┐
│                   FastAPI Backend                      │
│   • POST /api/upload       (Parses & chunks PDF)       │
│   • POST /api/chat         (RAG Retrieval & Synthesis) │
│   • GET  /api/documents    (List active index)         │
│   • GET  /docs             (Auto-generated Swagger UI) │
└──────────────────────────▲─────────────────────────────┘
                           │
      ┌────────────────────┴────────────────────┐
      │                                         │
┌─────▼────────────────────┐      ┌─────────────▼────────────┐
│      RAG Engine          │      │    LLM Synthesis Engine  │
│ • pypdf text extraction  │      │ • Gemini 2.5 Flash       │
│ • Overlapping chunking   │      │ • Zero-hallucination     │
│ • BM25 / TF-IDF ranking  │      │ • Offline fallback mode  │
└──────────────────────────┘      └──────────────────────────┘
```

---

## 🚀 How to Run the App (Tomorrow Morning or Tonight)

### Option 1: 1-Click Launch (Recommended)
Double-click **`run_app.bat`** in this folder.
- Starts the FastAPI backend.
- Serves the built React application at `http://localhost:8000`.
- Automatically opens your default web browser.

### Option 2: Live Development Mode
Double-click **`run_dev.bat`**.
- Starts FastAPI on port `8000`.
- Starts Vite React Dev Server on port `5173` with instant hot-reloading.

---

## 🎯 Live Demo Walkthrough for Interviewers

1. **Launch the App**: Double-click `run_app.bat`.
2. **Show the Swagger API Docs**: 
   - Open `http://localhost:8000/docs` in a tab to show the interviewer your clean FastAPI REST endpoints (`/api/upload`, `/api/chat`, `/api/health`). Interviewers love seeing Swagger documentation!
3. **Upload the Sample PDF**:
   - Return to the React app (`http://localhost:8000`).
   - Click the upload area and select `sample_project_report.pdf` (already created in the project folder).
4. **Point Out Real-time Metrics**:
   - Point to the document card: *3 Pages, 300+ Words, 4 Semantic Chunks, System Status: Ready*.
5. **Show 1-Click Actions**:
   - Click **"📋 Summarize Document"** or **"🔑 Key Takeaways"**.
6. **Ask Specific Technical Questions**:
   - Query 1: *"What GPUs are used and what is the query latency?"*
   - Query 2: *"What security protocols and data privacy standards are implemented?"*
   - Query 3: *"What is the projected revenue target for 2026?"*
7. **Expand Verified Sources**:
   - Click the **"📍 Verified Sources"** accordion under any answer to show the exact page number and text snippet.

---

## 🧠 Interview Talking Points & Questions

### 1. Elevator Pitch
> *"I built **DocuChat AI**, a decoupled full-stack application with a **React** interface and a high-performance **FastAPI** backend. It uses **Retrieval-Augmented Generation (RAG)** to index PDF documents into semantic chunks, scores them via term-frequency weighting, and generates answers strictly grounded in document context with verifiable page citations."*

### 2. Frontend Highlights (React)
- **Component Design**: Modular structure with real-time health polling, reactive state management, and file drag-and-drop.
- **User Experience**: Interactive citation drawers, latency metrics per message, engine switching (Gemini vs. Zero-dependency Offline Mode).

### 3. Backend Highlights (FastAPI)
- **Asynchronous endpoints**: Built with Pydantic schemas for request validation.
- **RAG Preprocessing**: Preserves original page coordinates and metadata during text extraction and chunk sliding-window generation.
- **Hallucination Defense**: Strict prompt boundaries prevent the model from answering questions outside the retrieved context.

---

## 📁 Project Structure

```
DocuChat/
├── backend/
│   ├── main.py                 # FastAPI application & REST endpoints
│   └── rag_engine.py           # PDF extraction, chunking, and search logic
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # React chat & upload interface
│   │   ├── index.css           # Modern design system styles
│   │   └── main.jsx            # React root entry point
│   ├── package.json            # Frontend dependencies & scripts
│   └── vite.config.js          # Vite configuration
├── sample_project_report.pdf   # Pre-generated 3-page tech report
├── run_app.bat                 # 1-Click full stack launcher
├── run_dev.bat                 # Developer launcher (FastAPI + Vite)
├── requirements.txt            # Python dependencies
└── README.md                   # Complete architectural guide
```
