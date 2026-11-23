"""
Creates a clean, valid multi-page PDF document without third-party dependencies.
This provides an instant sample document you can use to test and demo the app.
"""

def create_simple_pdf(filename="sample_project_report.pdf"):
    # Content for 3 pages
    pages_text = [
        [
            "PROJECT TITAN: NEXT-GENERATION ARTIFICIAL INTELLIGENCE PLATFORM",
            "",
            "1. EXECUTIVE SUMMARY",
            "Project Titan is an enterprise-grade artificial intelligence engine designed to",
            "automate workflow synthesis, intelligent data extraction, and real-time decision support.",
            "Launched in Q1 2026, the system reduces manual document processing time by 74%",
            "across distributed engineering and operations teams.",
            "",
            "2. CORE ARCHITECTURE",
            "The platform leverages Retrieval-Augmented Generation (RAG) coupled with a hybrid",
            "search indexing system. Documents are broken down into semantic chunks of 150 words.",
            "These chunks are indexed using an inverted term-frequency matrix for rapid sub-50ms",
            "retrieval before passing candidate passages to high-capacity language models.",
            "",
            "3. HARDWARE SPECIFICATIONS",
            "The server cluster runs on 16 interconnected NVIDIA H100 GPUs with high-bandwidth memory.",
            "Average latency per query is 120 milliseconds with 99.98% system uptime."
        ],
        [
            "SECURITY, COMPLIANCE, AND DATA PRIVACY",
            "",
            "4. SECURITY PROTOCOLS",
            "Security is enforced at every layer of Project Titan. All data in transit is encrypted",
            "using TLS 1.3 with AES-256-GCM cipher suites. At rest, database partitions utilize",
            "hardware-level encryption keys rotated automatically every 90 days.",
            "",
            "5. ACCESS CONTROL & AUDITING",
            "Role-Based Access Control (RBAC) restricts sensitive document retrieval to authorized",
            "personnel only. Audit logs record every prompt, response timestamp, and token count",
            "to comply with SOC-2 Type II and ISO 27001 certifications.",
            "",
            "6. HALLUCINATION PREVENTION",
            "To eliminate false outputs, strict context grounding restricts the model from",
            "generating claims not directly corroborated by retrieved citation passages.",
            "If an answer cannot be located, the system returns an explicit refusal message."
        ],
        [
            "FINANCIAL PERFORMANCE AND 2026 ROADMAP",
            "",
            "7. FINANCIAL METRICS (2025 - 2026)",
            "- Total R&D Expenditure: $4.2 Million",
            "- Operating Cost Savings: $11.8 Million annually across client deployments",
            "- Return on Investment (ROI): 280% realized within the first 6 months",
            "- Target Revenue for Fiscal Year 2026: $28.5 Million",
            "",
            "8. FUTURE MILESTONES",
            "- Q2 2026: Multimodal integration supporting audio transcription and diagram OCR.",
            "- Q3 2026: On-premise offline deployment package for air-gapped defense networks.",
            "- Q4 2026: Autonomous agent workflows capable of multi-database query synthesis."
        ]
    ]

    objects = []
    
    # Obj 1: Catalog
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    
    # Obj 2: Pages (filled later)
    # Obj 3: Font
    font_obj_idx = 3
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    
    page_obj_indices = []
    content_obj_indices = []
    
    curr_obj_id = 4
    for p_lines in pages_text:
        page_id = curr_obj_id
        content_id = curr_obj_id + 1
        page_obj_indices.append(page_id)
        content_obj_indices.append(content_id)
        curr_obj_id += 2

    # Fill Pages root object (Obj 2)
    kids_str = " ".join([f"{pid} 0 R" for pid in page_obj_indices])
    pages_root = f"<< /Type /Pages /Kids [ {kids_str} ] /Count {len(pages_text)} >>"
    
    # We build the file structure
    all_objs = {
        1: objects[0],
        2: pages_root,
        3: objects[1]
    }

    for p_idx, p_lines in enumerate(pages_text):
        page_id = page_obj_indices[p_idx]
        content_id = content_obj_indices[p_idx]
        
        # Build stream content
        stream_lines = ["BT", "/F1 11 Tf", "50 750 Td", "16 TL"]
        for line in p_lines:
            safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            if line.isupper() and len(line) > 5:
                # bold-ish effect by setting font size bigger
                stream_lines.append(f"ET BT /F1 13 Tf ({safe_line}) Tj T* /F1 11 Tf")
            else:
                stream_lines.append(f"({safe_line}) Tj T*")
        stream_lines.append("ET")
        stream_data = "\n".join(stream_lines).encode("latin-1")
        
        # Content object
        all_objs[content_id] = f"<< /Length {len(stream_data)} >>\nstream\n{stream_data.decode('latin-1')}\nendstream"
        
        # Page object
        all_objs[page_id] = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"

    # Assemble PDF with cross-reference table
    output = bytearray(b"%PDF-1.4\n")
    xref_offsets = [0]
    
    sorted_ids = sorted(all_objs.keys())
    for obj_id in sorted_ids:
        offset = len(output)
        xref_offsets.append(offset)
        output.extend(f"{obj_id} 0 obj\n{all_objs[obj_id]}\nendobj\n".encode("latin-1"))

    xref_start = len(output)
    output.extend(f"xref\n0 {len(sorted_ids) + 1}\n0000000000 65535 f \n".encode("latin-1"))
    for offset in xref_offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    output.extend(
        f"trailer\n<< /Size {len(sorted_ids) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("latin-1")
    )

    with open(filename, "wb") as f:
        f.write(output)

    print(f"Successfully generated sample PDF: {filename} ({len(pages_text)} pages)")


if __name__ == "__main__":
    create_simple_pdf()
