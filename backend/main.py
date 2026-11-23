import os
import time
import uuid
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from rag_engine import (
    extract_pdf_pages,
    chunk_pages,
    rank_chunks,
    generate_local_model_answer,
    load_local_model
)

app = FastAPI(
    title="DocuChat AI - Local On-Device RAG Platform",
    description="Local AI-powered document research assistant running 100% on-device.",
    version="2.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory document store
DOCUMENTS_STORE = {}


@app.on_event("startup")
def startup_event():
    """Pre-warm local model into memory on startup."""
    print("[DocuChat] Initializing local on-device AI model...")
    load_local_model()


class ChatRequest(BaseModel):
    doc_id: str
    question: str
    mode: Optional[str] = "local"
    api_key: Optional[str] = None


class SourceItem(BaseModel):
    id: int
    page: int
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    latency_ms: float
    mode_used: str


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "DocuChat AI Local Backend",
        "model": "Qwen 2.5 (0.5B-Instruct - On-Device)",
        "documents_loaded": len(DOCUMENTS_STORE)
    }


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Accepts a PDF file, parses pages, chunks content, and stores index."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        pages_data, total_words = extract_pdf_pages(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")

    if not pages_data:
        raise HTTPException(status_code=400, detail="No readable text could be extracted from this PDF.")

    chunks = chunk_pages(pages_data)
    doc_id = str(uuid.uuid4())[:8]

    DOCUMENTS_STORE[doc_id] = {
        "id": doc_id,
        "filename": file.filename,
        "pages_count": len(pages_data),
        "total_words": total_words,
        "chunks": chunks,
        "pages_data": pages_data
    }

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "pages_count": len(pages_data),
        "total_words": total_words,
        "chunks_count": len(chunks)
    }


@app.get("/api/documents")
def list_documents():
    """Lists all active indexed documents."""
    return [
        {
            "id": doc["id"],
            "filename": doc["filename"],
            "pages_count": doc["pages_count"],
            "total_words": doc["total_words"],
            "chunks_count": len(doc["chunks"])
        }
        for doc in DOCUMENTS_STORE.values()
    ]


@app.post("/api/chat", response_model=ChatResponse)
def chat_with_doc(req: ChatRequest):
    """Answers a question grounded in the specified document using the Local Model."""
    if req.doc_id not in DOCUMENTS_STORE:
        raise HTTPException(status_code=404, detail="Document not found. Please upload a PDF first.")

    doc = DOCUMENTS_STORE[req.doc_id]
    chunks = doc["chunks"]

    start_time = time.time()
    top_chunks = rank_chunks(req.question, chunks, top_k=3)

    # Run Local On-Device AI Generation
    answer = generate_local_model_answer(top_chunks, req.question)
    latency_ms = round((time.time() - start_time) * 1000, 2)

    return ChatResponse(
        answer=answer,
        sources=[SourceItem(id=c["id"], page=c["page"], text=c["text"]) for c in top_chunks],
        latency_ms=latency_ms,
        mode_used="Qwen 2.5 On-Device AI"
    )


# Serve Built React Frontend Static Files if available
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "dist"))

if os.path.exists(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def serve_frontend_root():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.get("/{catchall:path}")
    def serve_frontend_routes(catchall: str):
        file_path = os.path.join(FRONTEND_DIST, catchall)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("========================================================")
    print("  Starting DocuChat AI (100% Local On-Device AI Model)  ")
    print("  Web App URL: http://localhost:8000                   ")
    print("========================================================")
    uvicorn.run(app, host="127.0.0.1", port=8000)
