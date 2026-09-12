"""
retrieval.py — PDF text extraction, chunking, and TF-IDF search.

This module handles the core "find relevant passages" logic:
  1. Extract text from uploaded PDFs (page by page).
  2. Split each page into smaller chunks for better retrieval.
  3. Build a TF-IDF index over all chunks.
  4. Given a query, return the top-k most relevant chunks.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pypdf import PdfReader


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    """A small piece of text tied back to its source PDF and page."""
    text: str
    source_file: str
    page_number: int  # 1-indexed


@dataclass
class SearchResult:
    """One search hit returned to the caller."""
    text: str
    source_file: str
    page_number: int
    score: float


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_file, filename: str) -> list[Chunk]:
    """
    Read a PDF and return a list of Chunks (one per page).
    Returns an empty list if the PDF has no extractable text.
    """
    chunks: list[Chunk] = []
    try:
        reader = PdfReader(pdf_file)
    except Exception:
        return chunks

    for page_idx, page in enumerate(reader.pages):
        try:
            raw = page.extract_text() or ""
        except Exception:
            raw = ""
        text = raw.strip()
        if not text:
            continue
        chunks.append(Chunk(
            text=text,
            source_file=filename,
            page_number=page_idx + 1,
        ))
    return chunks


def split_chunks(chunks: list[Chunk], max_chars: int = 800) -> list[Chunk]:
    """
    Break large page-level chunks into smaller pieces so that
    retrieval is more precise.  We split on paragraph boundaries
    (double newline) first, then on sentence boundaries if needed.
    Each sub-chunk keeps the same source_file and page_number.
    """
    result: list[Chunk] = []
    for chunk in chunks:
        paragraphs = re.split(r"\n{2,}", chunk.text)
        buffer = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(buffer) + len(para) + 1 > max_chars and buffer:
                result.append(Chunk(buffer.strip(), chunk.source_file, chunk.page_number))
                buffer = ""
            buffer += para + "\n"
        if buffer.strip():
            result.append(Chunk(buffer.strip(), chunk.source_file, chunk.page_number))
    return result


# ---------------------------------------------------------------------------
# Simple TF-IDF engine (no external vector-DB dependency)
# ---------------------------------------------------------------------------

_STOPWORDS = set(
    "a an the is are was were be been being have has had do does did "
    "will would shall should may might can could of in to for on with "
    "at by from as into through during before after above below between "
    "and but or nor not so yet both either neither each every all any "
    "few more most other some such no only own same than too very it "
    "its this that these those i me my we our you your he him his she "
    "her they them their what which who whom how when where why".split()
)


def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, remove stopwords."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


class TFIDFIndex:
    """
    A bare-bones TF-IDF index that lives entirely in memory.
    Good enough for a few hundred pages of lecture material.
    """

    def __init__(self):
        self.chunks: list[Chunk] = []
        self.doc_freqs: Counter = Counter()       # token -> num docs containing it
        self.tf_vectors: list[dict[str, float]] = []  # per-doc TF vectors
        self._built = False

    # -- building the index --------------------------------------------------

    def add_chunks(self, chunks: list[Chunk]):
        """Add chunks to the index (call build() afterwards)."""
        self.chunks.extend(chunks)

    def build(self):
        """Compute TF and IDF values for all stored chunks."""
        self.doc_freqs = Counter()
        self.tf_vectors = []
        for chunk in self.chunks:
            tokens = _tokenize(chunk.text)
            tf = Counter(tokens)
            total = len(tokens) or 1
            tf_norm = {t: c / total for t, c in tf.items()}
            self.tf_vectors.append(tf_norm)
            for t in set(tokens):
                self.doc_freqs[t] += 1
        self._built = True

    # -- querying ------------------------------------------------------------

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Return the top-k chunks most relevant to *query*."""
        if not self._built or not self.chunks:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        n = len(self.chunks)
        # IDF for query terms
        idf = {}
        for t in set(query_tokens):
            df = self.doc_freqs.get(t, 0)
            idf[t] = math.log((n + 1) / (df + 1)) + 1   # smoothed IDF

        # query TF-IDF vector
        qtf = Counter(query_tokens)
        q_total = len(query_tokens) or 1
        q_vec = {t: (qtf[t] / q_total) * idf.get(t, 0) for t in set(query_tokens)}

        # score each document
        scores: list[tuple[int, float]] = []
        for idx, tf_vec in enumerate(self.tf_vectors):
            dot = 0.0
            for t, q_w in q_vec.items():
                dot += q_w * tf_vec.get(t, 0) * idf.get(t, 0)
            if dot > 0:
                scores.append((idx, dot))

        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scores[:top_k]:
            c = self.chunks[idx]
            results.append(SearchResult(
                text=c.text,
                source_file=c.source_file,
                page_number=c.page_number,
                score=score,
            ))
        return results

    @property
    def is_empty(self) -> bool:
        return len(self.chunks) == 0
