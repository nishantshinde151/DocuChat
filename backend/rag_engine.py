import os
import re
import math
import time
from collections import Counter
from pypdf import PdfReader

# Suppress HuggingFace symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Upgraded to Qwen 2.5 (State of the Art on-device model)
LOCAL_MODEL = None
LOCAL_TOKENIZER = None
LOCAL_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"


def load_local_model():
    """Loads and caches the high-accuracy Qwen 2.5 model in memory."""
    global LOCAL_MODEL, LOCAL_TOKENIZER
    if LOCAL_MODEL is not None and LOCAL_TOKENIZER is not None:
        return LOCAL_MODEL, LOCAL_TOKENIZER
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        print(f"[DocuChat] Loading high-performance local AI: {LOCAL_MODEL_ID}...")
        tok = AutoTokenizer.from_pretrained(LOCAL_MODEL_ID)
        mod = AutoModelForCausalLM.from_pretrained(LOCAL_MODEL_ID)
        LOCAL_TOKENIZER = tok
        LOCAL_MODEL = mod
        print("[DocuChat] Qwen 2.5 On-Device Model is ready!")
        return LOCAL_MODEL, LOCAL_TOKENIZER
    except Exception as e:
        print(f"[DocuChat] Model loading error: {e}")
        return None, None


def extract_pdf_pages(file_bytes):
    """Extracts text from PDF file bytes and retains page numbers."""
    from io import BytesIO
    reader = PdfReader(BytesIO(file_bytes))
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
    """Splits pages into overlapping text chunks with source page metadata."""
    chunks = []
    chunk_id = 0
    for page_info in pages_data:
        words = page_info["text"].split()
        page_num = page_info["page_num"]
        
        if len(words) <= chunk_size:
            chunk_id += 1
            chunks.append({
                "id": chunk_id,
                "page": page_num,
                "text": " ".join(words)
            })
        else:
            step = chunk_size - overlap
            for i in range(0, len(words), step):
                chunk_words = words[i:i + chunk_size]
                if len(chunk_words) > 20:
                    chunk_id += 1
                    chunks.append({
                        "id": chunk_id,
                        "page": page_num,
                        "text": " ".join(chunk_words)
                    })
    return chunks


def tokenize(text):
    return re.findall(r"\b[a-zA-Z0-9_]{3,}\b", text.lower())


def rank_chunks(query, chunks, top_k=3):
    """BM25/TF-IDF term weighting retrieval."""
    query_tokens = tokenize(query)
    if not query_tokens or not chunks:
        return chunks[:top_k]

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
                df = doc_freq.get(token, 0)
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                score += tf * idf
        
        scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    results = [item[1] for item in scored_chunks[:top_k]]
    
    if all(s[0] == 0 for s in scored_chunks[:top_k]) and chunks:
        return chunks[:top_k]
    return results


def generate_local_model_answer(context_chunks, user_question):
    """
    Synthesizes rich, fluent, natural answers using Qwen 2.5 (0.5B) on CPU.
    """
    model, tok = load_local_model()
    if model is None or tok is None:
        return generate_extractive_answer(context_chunks, user_question)

    # Clean and assemble context
    context_str = ""
    pages_used = []
    for c in context_chunks:
        pages_used.append(str(c["page"]))
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f\u25a1\uf0b7\uf0a7\u2022]', ' ', c["text"])
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        context_str += f"[Page {c['page']}]: {cleaned[:350]}\n"

    system_instruction = (
        "You are DocuChat AI, a senior research analyst. "
        "Answer the user's question clearly, concisely, and accurately using ONLY the provided document context below. "
        "Highlight important concepts in bold. If there are multiple key points, format them as clean bullet points.\n\n"
        f"DOCUMENT CONTEXT:\n{context_str}"
    )

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"Question: {user_question}"}
    ]

    try:
        prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tok(prompt, return_tensors="pt")
        
        outputs = model.generate(
            **inputs,
            max_new_tokens=180,
            do_sample=False,
            repetition_penalty=1.12
        )
        
        generated_text = tok.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
        
        # Clean markdown output
        pages_list = ", ".join(sorted(set(pages_used), key=lambda x: int(x)))
        response_lines = [
            generated_text,
            "\n---",
            f"**Verified Sources:** Pages {pages_list} *(Grounded with Qwen 2.5 On-Device AI)*"
        ]
        return "\n".join(response_lines)
    except Exception as e:
        print(f"[DocuChat] Generation notice: {e}")
        return generate_extractive_answer(context_chunks, user_question)


def generate_extractive_answer(context_chunks, user_question):
    """Deterministic fallback."""
    query_words = set(tokenize(user_question))
    clean_points = []
    referenced_pages = set()
    
    for c in context_chunks:
        referenced_pages.add(str(c["page"]))
        cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f\u25a1\uf0b7\uf0a7\u2022]', ' ', c["text"])
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned_text) if len(s.strip()) > 18]
        
        scored_sentences = []
        for s in sentences:
            s_words = set(tokenize(s))
            overlap = len(query_words.intersection(s_words))
            scored_sentences.append((overlap, s))
        
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top = [item[1] for item in scored_sentences[:2]] if scored_sentences else sentences[:2]
        for s in top:
            s_clean = s.strip().strip('"').strip("'")
            if s_clean and s_clean not in [p[1] for p in clean_points]:
                clean_points.append((c["page"], s_clean))
    
    lines = ["### Key Findings from Document\n"]
    for page_num, text_point in clean_points[:4]:
        if not text_point.endswith('.'):
            text_point += '.'
        lines.append(f"- **{text_point}** *(Source: Page {page_num})*")
    
    pages_str = ", ".join(sorted(referenced_pages, key=lambda x: int(x)))
    lines.append(f"\n---\n**Verified Sources:** Pages {pages_str}")
    return "\n".join(lines)
