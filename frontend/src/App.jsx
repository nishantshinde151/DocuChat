import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import {
  FileText,
  UploadCloud,
  Send,
  Sparkles,
  Bot,
  User,
  ShieldCheck,
  Zap,
  ChevronDown,
  ChevronUp,
  Cpu,
  CheckCircle,
  HelpCircle,
  Search,
  ExternalLink
} from "lucide-react";

const BACKEND_URL = "http://localhost:8000";

export default function App() {
  const [doc, setDoc] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [mode, setMode] = useState("gemini"); // "gemini" or "offline"
  const [apiKey, setApiKey] = useState(localStorage.getItem("docuchat_api_key") || "");
  const [backendStatus, setBackendStatus] = useState("checking");
  const [expandedSources, setExpandedSources] = useState({});

  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Check backend health on mount
  useEffect(() => {
    fetch(`${BACKEND_URL}/api/health`)
      .then((res) => res.json())
      .then(() => setBackendStatus("connected"))
      .catch(() => setBackendStatus("disconnected"));
  }, []);

  const handleApiKeyChange = (val) => {
    setApiKey(val);
    localStorage.setItem("docuchat_api_key", val);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Please upload a PDF file.");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${BACKEND_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }

      const data = await res.json();
      setDoc(data);
      setMessages([
        {
          role: "assistant",
          content: `✅ Successfully indexed **${data.filename}** (${data.pages_count} pages, ${data.chunks_count} chunks). What would you like to know about this document?`,
        },
      ]);
    } catch (err) {
      alert(`Error uploading document: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const sendMessage = async (queryText) => {
    const query = queryText || input;
    if (!query.trim() || !doc || loading) return;

    const userMsg = { role: "user", content: query };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doc_id: doc.doc_id,
          question: query,
          mode: mode,
          api_key: apiKey,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Query failed");
      }

      const data = await res.json();
      const assistantMsg = {
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        latency_ms: data.latency_ms,
        mode_used: data.mode_used,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ Failed to get answer: ${err.message}. Please check if the FastAPI backend is running.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSources = (index) => {
    setExpandedSources((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Bot size={22} />
          </div>
          <div>
            <div className="brand-title">
              DocuChat <span className="brand-badge">RAG AI</span>
            </div>
          </div>
        </div>

        {/* Engine Mode */}
        <div style={{ background: "#ecfdf5", border: "1px solid #a7f3d0", padding: "12px", borderRadius: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#065f46", fontWeight: "700", fontSize: "0.82rem" }}>
            <Cpu size={16} color="#059669" /> Qwen 2.5 On-Device AI
          </div>
          <p style={{ fontSize: "0.72rem", color: "#047857", marginTop: "4px", lineHeight: "1.3" }}>
            High-reasoning 0.5B model running 100% locally on CPU. Zero API keys, zero internet calls, and no rate limits.
          </p>
        </div>

        {/* Document Upload */}
        <div>
          <div className="section-label">Active Document</div>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: "none" }}
            accept=".pdf"
            onChange={handleFileUpload}
          />

          {!doc ? (
            <div
              className={`dropzone ${uploading ? "active" : ""}`}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud size={28} className="dropzone-icon" />
              <div className="dropzone-text">
                {uploading ? "Indexing PDF..." : "Upload PDF Document"}
              </div>
              <div className="dropzone-sub">Click to browse or drag & drop</div>
            </div>
          ) : (
            <div className="doc-card">
              <div className="doc-header">
                <FileText size={20} color="var(--primary)" />
                <span className="doc-name" title={doc.filename}>
                  {doc.filename}
                </span>
              </div>
              <div className="doc-stats">
                <div className="stat-pill">
                  <span className="stat-label">Pages</span>
                  <span className="stat-val">{doc.pages_count}</span>
                </div>
                <div className="stat-pill">
                  <span className="stat-label">Words</span>
                  <span className="stat-val">{doc.total_words?.toLocaleString()}</span>
                </div>
                <div className="stat-pill">
                  <span className="stat-label">Chunks</span>
                  <span className="stat-val">{doc.chunks_count}</span>
                </div>
                <div className="stat-pill">
                  <span className="stat-label">Status</span>
                  <span className="stat-val" style={{ color: "var(--success)" }}>Ready</span>
                </div>
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                style={{
                  marginTop: "10px",
                  width: "100%",
                  padding: "6px",
                  fontSize: "0.75rem",
                  background: "#f1f5f9",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  cursor: "pointer",
                  color: "#475569",
                  fontWeight: 600,
                }}
              >
                Upload Different PDF
              </button>
            </div>
          )}
        </div>

        {/* Interview Talking Points */}
        <div className="interview-box">
          <strong>🎯 Interview Talking Points:</strong>
          • Full-stack Architecture: React + FastAPI<br />
          • Retrieval: BM25/TF-IDF token scoring<br />
          • Synthesis: Context-bounded LLM prompting<br />
          • Hallucination Defense: Exact citations & page attribution
        </div>
      </aside>

      {/* Main Chat */}
      <main className="main-chat">
        {/* Top Navbar */}
        <header className="top-bar">
          <div className="top-title">
            <span>DocuChat Assistant</span>
            {doc && (
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 400 }}>
                • {doc.filename}
              </span>
            )}
          </div>
          <div className="status-badge">
            <span
              className="status-dot"
              style={{
                backgroundColor: backendStatus === "connected" ? "var(--success)" : "#ef4444",
              }}
            />
            {backendStatus === "connected" ? "FastAPI Backend :8000" : "Connecting Backend..."}
          </div>
        </header>

        {/* Messages or Welcome Hero */}
        {!doc ? (
          <div className="empty-hero">
            <div className="hero-icon">
              <FileText size={28} />
            </div>
            <h1 className="hero-title">Talk to Any PDF Document</h1>
            <p className="hero-sub">
              Upload any PDF report, contract, or paper to ask questions, generate instant
              bullet-point summaries, and view exact citations.
            </p>
            <div className="feature-grid">
              <div className="feature-card">
                <Search size={18} color="var(--primary)" />
                <div className="feature-title">Precision Retrieval</div>
                <div className="feature-desc">
                  Isolates top-K relevant chunks using semantic search and term frequency.
                </div>
              </div>
              <div className="feature-card">
                <ShieldCheck size={18} color="var(--accent)" />
                <div className="feature-title">Grounded Citations</div>
                <div className="feature-desc">
                  Every answer references original page numbers to eliminate hallucinations.
                </div>
              </div>
              <div className="feature-card">
                <Zap size={18} color="#eab308" />
                <div className="feature-title">FastAPI + React</div>
                <div className="feature-desc">
                  Decoupled full-stack architecture with sub-100ms local retrieval latency.
                </div>
              </div>
            </div>
            <button
              onClick={() => fileInputRef.current?.click()}
              style={{
                marginTop: "28px",
                padding: "12px 24px",
                background: "var(--primary)",
                color: "white",
                border: "none",
                borderRadius: "10px",
                fontWeight: 600,
                fontSize: "0.95rem",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                boxShadow: "0 4px 12px rgba(37, 99, 235, 0.3)",
              }}
            >
              <UploadCloud size={18} /> Select Sample PDF to Begin
            </button>
          </div>
        ) : (
          <div className="messages-container">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className={`msg-avatar ${msg.role}`}>
                  {msg.role === "user" ? <User size={18} /> : <Bot size={18} />}
                </div>
                <div className="msg-content-wrapper">
                  <div className="msg-bubble">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>

                  {msg.role === "assistant" && msg.latency_ms && (
                    <div className="msg-meta">
                      <span>⚡ {msg.latency_ms}ms</span>
                      <span>•</span>
                      <span>Mode: {msg.mode_used}</span>
                    </div>
                  )}

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="sources-accordion">
                      <div
                        className="sources-header"
                        onClick={() => toggleSources(idx)}
                      >
                        <span>
                          📍 Verified Sources ({msg.sources.length} chunks referenced)
                        </span>
                        {expandedSources[idx] ? (
                          <ChevronUp size={16} />
                        ) : (
                          <ChevronDown size={16} />
                        )}
                      </div>

                      {expandedSources[idx] && (
                        <div className="sources-list">
                          {msg.sources.map((s, sIdx) => (
                            <div key={sIdx} className="source-item">
                              <span className="source-badge">Page {s.page}</span>
                              <span>"{s.text.slice(0, 300)}..."</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="message assistant">
                <div className="msg-avatar assistant">
                  <Bot size={18} />
                </div>
                <div className="msg-content-wrapper">
                  <div className="msg-bubble" style={{ color: "var(--text-muted)" }}>
                    <Sparkles size={16} style={{ display: "inline", marginRight: "6px" }} />
                    Retrieving passages & synthesizing answer...
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Quick Action Chips */}
        {doc && (
          <div className="quick-chips">
            <button
              className="chip-btn"
              onClick={() =>
                sendMessage("Provide a comprehensive executive summary of this document.")
              }
            >
              <Sparkles size={14} color="#eab308" /> Summarize Document
            </button>
            <button
              className="chip-btn"
              onClick={() =>
                sendMessage("What are the key facts, findings, and conclusions?")
              }
            >
              <CheckCircle size={14} color="var(--success)" /> Key Takeaways
            </button>
            <button
              className="chip-btn"
              onClick={() =>
                sendMessage("What are 3 interesting questions someone should ask about this document?")
              }
            >
              <HelpCircle size={14} color="var(--primary)" /> Suggested Questions
            </button>
          </div>
        )}

        {/* Bottom Input Area */}
        {doc && (
          <div className="chat-input-area">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                sendMessage();
              }}
              className="input-bar"
            >
              <input
                type="text"
                className="chat-input"
                placeholder="Ask any question about this document (e.g. 'What are the security protocols?')..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="send-btn"
                disabled={!input.trim() || loading}
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}
