"""
app.py — StudyMate: Ask questions from your lecture notes.

A Streamlit app that lets students upload lecture PDFs, extracts and indexes
the text, and answers natural-language questions using TF-IDF retrieval.
"""

import os
import streamlit as st
from dotenv import load_dotenv

import retrieval
from retrieval import (
    Chunk,
    SearchResult,
    TFIDFIndex,
    extract_text_from_pdf,
    split_chunks,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

st.set_page_config(
    page_title="StudyMate",
    page_icon="📚",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS — clean, modern, student-project feel
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* --- Global tweaks --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header area */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #555;
        margin-top: 0.2rem;
        margin-bottom: 1.5rem;
    }

    /* Answer card */
    .answer-card {
        background: #f8f9fb;
        border-left: 4px solid #4361ee;
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        margin: 1rem 0;
        line-height: 1.7;
        color: #222;
    }

    /* Source card */
    .source-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
    }
    .source-header {
        font-weight: 600;
        color: #4361ee;
        margin-bottom: 0.4rem;
        font-size: 0.95rem;
    }
    .source-passage {
        color: #444;
        font-size: 0.88rem;
        border-left: 3px solid #ddd;
        padding-left: 0.8rem;
        margin-top: 0.3rem;
        line-height: 1.6;
    }

    /* Not-found banner */
    .not-found {
        background: #fff8e1;
        border-left: 4px solid #f9a825;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 1rem 0;
    }
    .not-found strong {
        color: #e65100;
    }

    /* Welcome card */
    .welcome-card {
        background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);
        border-radius: 12px;
        padding: 2.5rem 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    .welcome-card h2 {
        color: #1a1a2e;
        margin-bottom: 0.5rem;
    }
    .welcome-card p {
        color: #555;
        max-width: 500px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* Sidebar tweaks */
    section[data-testid="stSidebar"] {
        background: #f4f6fa;
    }
    section[data-testid="stSidebar"] h1 {
        font-size: 1.3rem;
    }

    /* Status chips */
    .status-ok {
        color: #2e7d32;
        font-weight: 500;
    }
    .status-warn {
        color: #e65100;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def _init_state():
    defaults = {
        "index": TFIDFIndex(),
        "processed": False,
        "file_names": [],
        "total_chunks": 0,
        "total_pages": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ---------------------------------------------------------------------------
# Answer Generation
# ---------------------------------------------------------------------------

def _get_ai_answer(question: str, context_passages: list[str]) -> str | None:
    """
    Call Google Gemini to synthesise an answer from the retrieved passages.
    Returns None if no API key is configured or the call fails.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        context = "\n\n---\n\n".join(context_passages)
        prompt = (
            "You are a helpful study assistant. Answer the student's question "
            "using ONLY the lecture material provided below. "
            "If the material does not contain enough information, reply exactly: "
            "\"I couldn't find enough information in the uploaded lectures to answer this.\" "
            "Do not make up facts. Be concise and clear. Use bullet points if helpful.\n\n"
            f"## Lecture Material\n\n{context}\n\n## Question\n\n{question}"
        )

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 📚 StudyMate")
    st.caption("Upload & process your lectures")

    st.markdown("---")

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload lecture PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Select one or more PDF files from your lectures.",
    )

    # Show uploaded file names
    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected**")
        for f in uploaded_files:
            st.text(f"  📄 {f.name}")
    else:
        st.info("No files uploaded yet.")

    st.markdown("---")

    # Process button
    process_btn = st.button(
        "⚙️ Process Documents",
        use_container_width=True,
        disabled=not uploaded_files,
    )

    if process_btn and uploaded_files:
        index = TFIDFIndex()
        all_names = []
        total_pages = 0
        warnings = []

        progress = st.progress(0, text="Extracting text…")
        for i, pdf_file in enumerate(uploaded_files):
            page_chunks = extract_text_from_pdf(pdf_file, pdf_file.name)
            if not page_chunks:
                warnings.append(f"⚠️ **{pdf_file.name}** — no extractable text found (scanned/empty PDF?).")
                continue
            total_pages += len(page_chunks)
            small_chunks = split_chunks(page_chunks)
            index.add_chunks(small_chunks)
            all_names.append(pdf_file.name)
            progress.progress((i + 1) / len(uploaded_files), text=f"Processing {pdf_file.name}…")

        if index.is_empty:
            st.error("No text could be extracted from any uploaded PDF.")
        else:
            index.build()
            st.session_state["index"] = index
            st.session_state["processed"] = True
            st.session_state["file_names"] = all_names
            st.session_state["total_chunks"] = len(index.chunks)
            st.session_state["total_pages"] = total_pages
            st.success(f"✅ Indexed **{total_pages}** pages from **{len(all_names)}** file(s).")

        for w in warnings:
            st.warning(w)

        progress.empty()

    # Status section
    st.markdown("---")
    st.markdown("##### Status")

    if st.session_state["processed"]:
        st.markdown(f'<span class="status-ok">● Documents loaded</span>', unsafe_allow_html=True)
        st.caption(
            f"{len(st.session_state['file_names'])} file(s) · "
            f"{st.session_state['total_pages']} pages · "
            f"{st.session_state['total_chunks']} chunks"
        )
    else:
        st.markdown(f'<span class="status-warn">● No documents processed</span>', unsafe_allow_html=True)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        st.markdown(f'<span class="status-ok">● Gemini API key set</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="status-warn">● No API key — fallback mode</span>', unsafe_allow_html=True)
        st.caption("Set GEMINI_API_KEY in .env for AI answers.")


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.markdown('<div class="main-title">📚 StudyMate</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Ask questions from your lecture notes — without searching through 100 slides.</div>',
    unsafe_allow_html=True,
)

# If nothing is processed yet, show a welcome message
if not st.session_state["processed"]:
    st.markdown("""
    <div class="welcome-card">
        <h2>👋 Welcome!</h2>
        <p>
            Upload your lecture PDFs in the sidebar and click
            <strong>Process Documents</strong> to get started.
            Then come back here to ask questions.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ----- Question input -----
st.markdown("### Ask a question")

question = st.text_input(
    "Type your question here",
    placeholder="e.g. What are the main principles of Total Quality Management?",
    label_visibility="collapsed",
)

ask_btn = st.button("🔍 Ask", use_container_width=False)

if ask_btn and question.strip():
    query = question.strip()

    # Check if the query is too vague (all stopwords or very short)
    import re as _re
    _query_tokens = [t for t in _re.findall(r"[a-z0-9]+", query.lower())
                     if t not in retrieval._STOPWORDS and len(t) > 1]
    if not _query_tokens:
        st.warning("Your question is too vague. Try asking something more specific, like: "
                   "*What are the main principles of Total Quality Management?*")
        st.stop()

    index: TFIDFIndex = st.session_state["index"]
    results: list[SearchResult] = index.search(query, top_k=5)

    # Filter to a reasonable relevance threshold
    if results:
        top_score = results[0].score
        # Keep results that are at least 30% of the top score
        results = [r for r in results if r.score >= top_score * 0.30]
        results = results[:3]  # show at most 3 sources

    if not results:
        # --- Unanswerable ---
        st.markdown("""
        <div class="not-found">
            <strong>Not found in your lecture material</strong><br>
            I couldn't find enough information in the uploaded lectures to answer this question.
        </div>
        """, unsafe_allow_html=True)
    else:
        # --- Answerable ---
        passages = [r.text for r in results]
        ai_answer = _get_ai_answer(query, passages)

        st.markdown("### Answer")

        if ai_answer:
            # Check if the AI itself said it can't answer
            cant_answer_phrases = [
                "couldn't find enough information",
                "could not find enough information",
                "not enough information",
                "don't have enough information",
                "no information available",
            ]
            if any(phrase in ai_answer.lower() for phrase in cant_answer_phrases):
                st.markdown("""
                <div class="not-found">
                    <strong>Not found in your lecture material</strong><br>
                    I couldn't find enough information in the uploaded lectures to answer this question.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="answer-card">{ai_answer}</div>', unsafe_allow_html=True)
        else:
            st.info("💡 *Showing the most relevant passages.*")
            for r in results:
                preview = r.text[:500] + ("…" if len(r.text) > 500 else "")
                st.markdown(f'<div class="answer-card">{preview}</div>', unsafe_allow_html=True)

        # --- Sources ---
        st.markdown("### Sources")
        for r in results:
            passage_preview = r.text[:300] + ("…" if len(r.text) > 300 else "")
            st.markdown(f"""
            <div class="source-card">
                <div class="source-header">📄 {r.source_file} — Page {r.page_number}</div>
                <div class="source-passage">{passage_preview}</div>
            </div>
            """, unsafe_allow_html=True)

elif ask_btn and not question.strip():
    st.warning("Please type a question first.")
