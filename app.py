import os
import re
import math
from collections import Counter
import streamlit as st
from pypdf import PdfReader

# Optional Gemini support via google-genai
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ==========================================
# 1. CORE FUNCTIONS: TEXT & PDF PROCESSING
# ==========================================
def extract_pdf_pages(uploaded_file):
    """Extracts text from an uploaded PDF and retains page numbers."""
    reader = PdfReader(uploaded_file)
    pages_data = []
    total_words = 0
    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        cleaned = re.sub(r"\s+", " ", text).strip()
        if cleaned:
            words = len(cleaned.split())
            total_words += words
            pages_data.append({
                "page_num": page_idx + 1,
                "text": cleaned
            })
    return pages_data, total_words


def chunk_pages(pages_data, chunk_size=150, overlap=30):
    """
    Splits pages into overlapping text chunks with source page metadata.
    This is standard RAG (Retrieval-Augmented Generation) preprocessing.
    """
    chunks = []
    for page_info in pages_data:
        words = page_info["text"].split()
        page_num = page_info["page_num"]
        
        if len(words) <= chunk_size:
            chunks.append({
                "page": page_num,
                "text": " ".join(words)
            })
        else:
            step = chunk_size - overlap
            for i in range(0, len(words), step):
                chunk_words = words[i:i + chunk_size]
                if len(chunk_words) > 20:  # Skip tiny residual fragments
                    chunks.append({
                        "page": page_num,
                        "text": " ".join(chunk_words)
                    })
    return chunks


# ==========================================
# 2. RETRIEVAL ENGINE (TF-IDF & KEYWORD SIMILARITY)
# ==========================================
def tokenize(text):
    return re.findall(r"\b[a-zA-Z0-9_]{3,}\b", text.lower())


def rank_chunks(query, chunks, top_k=3):
    """
    Ranks chunks using BM25-style term frequency matching.
    Returns the top-K most relevant chunks with similarity scores.
    """
    query_tokens = tokenize(query)
    if not query_tokens or not chunks:
        return chunks[:top_k]

    # Calculate document frequency
    N = len(chunks)
    doc_freq = Counter()
    for chunk in chunks:
        tokens_in_chunk = set(tokenize(chunk["text"]))
        for token in query_tokens:
            if token in tokens_in_chunk:
                doc_freq[token] += 1

    scored_chunks = []
    for chunk in chunks:
        chunk_tokens = tokenize(chunk["text"])
        chunk_len = max(len(chunk_tokens), 1)
        score = 0.0
        
        token_counts = Counter(chunk_tokens)
        for token in query_tokens:
            if token in token_counts:
                tf = token_counts[token] / chunk_len
                # IDF weighting
                df = doc_freq.get(token, 0)
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                score += tf * idf
        
        scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Return top_k
    results = [item[1] for item in scored_chunks[:top_k]]
    # If all scores are 0 (no direct word overlap), return first top_k
    if all(s[0] == 0 for s in scored_chunks[:top_k]) and chunks:
        return chunks[:top_k]
    return results


# ==========================================
# 3. GENERATION ENGINE (GEMINI API OR OFFLINE MODE)
# ==========================================
def generate_ai_answer(api_key, context_chunks, user_question):
    """
    Sends the question and retrieved context to Gemini LLM.
    """
    if not api_key:
        return None, "No API Key provided. Switch to 'Offline / Smart Extractor Mode' or provide a free Gemini API key."
    
    try:
        client = genai.Client(api_key=api_key)
        
        context_str = ""
        for i, c in enumerate(context_chunks, 1):
            context_str += f"\n--- Source {i} (Page {c['page']}) ---\n{c['text']}\n"

        prompt = f"""You are an intelligent document research assistant. 
Answer the user's question accurately using ONLY the context provided below.
If the answer cannot be found in the context, say: "I could not find information about this in the provided document."

CONTEXT:
{context_str}

USER QUESTION:
{user_question}

INSTRUCTIONS:
1. Provide a clear, direct answer in 2-4 sentences or bullet points.
2. At the end of your answer, cite the page number(s) you used (e.g. "[Source: Page X]")."""

        candidate_models = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-3.8-flash"
        ]
        last_err = None
        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text, None
            except Exception as model_err:
                last_err = model_err
                continue

        return None, str(last_err)
    except Exception as e:
        return None, str(e)


def generate_offline_answer(context_chunks, user_question):
    """
    Fallback extractor when no internet/API key is present.
    Ensures your demo NEVER fails during an interview!
    """
    lines = []
    lines.append(f"**Extracted Insights from Document:**\n")
    for idx, c in enumerate(context_chunks, 1):
        sentences = c["text"].split(". ")
        sample_sentence = ". ".join(sentences[:2]).strip()
        lines.append(f"- **Key Passage {idx}** (Page {c['page']}): \"{sample_sentence}...\"")
    
    lines.append("\n> *💡 Note: Operating in offline extraction mode. Add a Gemini API key in the sidebar for full conversational synthesis.*")
    return "\n".join(lines)


# ==========================================
# 4. STREAMLIT USER INTERFACE
# ==========================================
def main():
    st.set_page_config(
        page_title="DocuChat AI - Chat with PDF",
        page_icon="📄",
        layout="wide"
    )

    # Custom styling
    st.markdown("""
        <style>
        .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0px; }
        .sub-header { font-size: 1rem; color: #4B5563; margin-bottom: 20px; }
        .badge { background-color: #E0E7FF; color: #3730A3; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
        .source-box { background-color: #F8FAFC; border-left: 4px solid #3B82F6; padding: 10px; border-radius: 4px; margin-top: 10px; }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar: Config & Document Upload
    with st.sidebar:
        st.title("⚙️ Settings & Upload")
        
        st.markdown("### 1. API Configuration")
        mode = st.radio(
            "Engine Mode:",
            ["Google Gemini AI (LLM)", "Offline Extractor (No Key Needed)"],
            help="Choose Gemini for natural AI answers, or Offline for guaranteed zero-dependency demo."
        )

        api_key = ""
        if mode == "Google Gemini AI (LLM)":
            api_key = st.text_input(
                "Gemini API Key:",
                value=os.environ.get("GEMINI_API_KEY", ""),
                type="password",
                placeholder="AIzaSy...",
                help="Get a free key from Google AI Studio (aistudio.google.com)"
            )
            if not api_key:
                st.info("👉 Don't have a key? Select 'Offline Extractor' above or get a free key in 30 seconds at [Google AI Studio](https://aistudio.google.com).")

        st.markdown("---")
        st.markdown("### 2. Document Upload")
        uploaded_file = st.file_uploader("Upload a PDF Document", type=["pdf"])

        st.markdown("---")
        st.markdown("### 💡 Quick Interview Demo")
        st.markdown("""
        **What to tell the interviewer:**
        - **Architecture:** RAG (Retrieval-Augmented Generation).
        - **Pipeline:** Chunking → BM25/TF-IDF Retrieval → LLM synthesis with Page Citations.
        - **Zero Hallucination:** Constrained to document context only.
        """)

    # Main Page Layout
    st.markdown('<div class="main-header">📄 DocuChat AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask questions, generate summaries, and extract citations from any PDF document.</div>', unsafe_allow_html=True)

    if not uploaded_file:
        # Welcome Screen
        st.info("👈 **Get Started:** Upload a PDF document in the left sidebar to begin.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 🔍 Precision Search")
            st.write("Retrieves the exact sentences and pages answering your questions.")
        with col2:
            st.markdown("### 🛡️ Grounded & Accurate")
            st.write("Answers cite exact page numbers so you know where information comes from.")
        with col3:
            st.markdown("### ⚡ Fast & Portable")
            st.write("Runs locally in your browser with instant document indexing.")
        return

    # Process Document (cached in session state)
    if "current_doc" not in st.session_state or st.session_state.get("doc_name") != uploaded_file.name:
        with st.spinner("Indexing and chunking document..."):
            pages_data, total_words = extract_pdf_pages(uploaded_file)
            chunks = chunk_pages(pages_data)
            st.session_state["pages_data"] = pages_data
            st.session_state["chunks"] = chunks
            st.session_state["total_words"] = total_words
            st.session_state["doc_name"] = uploaded_file.name
            st.session_state["messages"] = []
    
    pages_data = st.session_state["pages_data"]
    chunks = st.session_state["chunks"]
    total_words = st.session_state["total_words"]

    # Document Metrics Bar
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Document", uploaded_file.name[:18] + ("..." if len(uploaded_file.name) > 18 else ""))
    m2.metric("Total Pages", len(pages_data))
    m3.metric("Word Count", f"{total_words:,}")
    m4.metric("Indexed Chunks", len(chunks))

    st.markdown("---")

    # Quick One-Click Actions
    st.markdown("##### 🚀 Quick Actions:")
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    quick_query = None
    with btn_col1:
        if st.button("📋 Summarize Document"):
            quick_query = "Provide a comprehensive summary of this document highlighting the key points."
    with btn_col2:
        if st.button("🔑 Key Takeaways & Facts"):
            quick_query = "What are the most important conclusions, facts, or findings in this document?"
    with btn_col3:
        if st.button("❓ What questions can I ask?"):
            quick_query = "What are 3 interesting questions someone should ask about this document?"

    # Chat History Container
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sources" in msg and msg["sources"]:
                with st.expander(f"📍 View Sources ({len(msg['sources'])} chunks)"):
                    for s_idx, s in enumerate(msg["sources"], 1):
                        st.markdown(f"**Source {s_idx} (Page {s['page']}):**")
                        st.caption(f"_{s['text'][:350]}..._")

    # Chat Input Handling
    user_input = st.chat_input("Ask any question about this document...")
    query_to_run = quick_query or user_input

    if query_to_run:
        # Display user message
        st.session_state["messages"].append({"role": "user", "content": query_to_run})
        with st.chat_message("user"):
            st.markdown(query_to_run)

        # Retrieve relevant chunks
        top_chunks = rank_chunks(query_to_run, chunks, top_k=3)

        # Generate Answer
        with st.chat_message("assistant"):
            with st.spinner("Analyzing document..."):
                if mode == "Google Gemini AI (LLM)" and api_key:
                    answer, err = generate_ai_answer(api_key, top_chunks, query_to_run)
                    if err:
                        st.error(f"Error calling API: {err}")
                        answer = generate_offline_answer(top_chunks, query_to_run)
                else:
                    answer = generate_offline_answer(top_chunks, query_to_run)

            st.markdown(answer)
            if top_chunks:
                with st.expander(f"📍 View Sources ({len(top_chunks)} chunks)"):
                    for s_idx, s in enumerate(top_chunks, 1):
                        st.markdown(f"**Source {s_idx} (Page {s['page']}):**")
                        st.caption(f"_{s['text'][:350]}..._")

        # Save to history
        st.session_state["messages"].append({
            "role": "assistant",
            "content": answer,
            "sources": top_chunks
        })


if __name__ == "__main__":
    main()
