# StudyMate 📚

A study assistant that lets you upload lecture PDFs and ask questions about their contents. Built for the "The Night Before" IT Geeks coding challenge.

Upload your slides, click process, and ask away — StudyMate finds the relevant passages and gives you a clear answer with page-level citations. No more scrolling through 100 slides at 2 AM.

## Features

- **PDF upload** — drag-and-drop one or more lecture PDFs
- **Text extraction** — pulls text from every page using PyPDF
- **Local search** — TF-IDF + cosine similarity ranks passages by relevance (no cloud vector DB required)
- **AI answers** — optional Gemini integration synthesises a concise answer from the retrieved passages
- **Source citations** — every answer shows the PDF filename, page number, and the relevant excerpt
- **Offline mode** — works without an API key by showing the best-matching raw passages
- **Honest answers** — if the material doesn't cover the question, it says so instead of making something up

## Tech Stack

| Layer        | Tool                |
|--------------|---------------------|
| Frontend     | Streamlit           |
| PDF parsing  | pypdf               |
| Retrieval    | TF-IDF (pure Python)|
| LLM          | Gemini API (optional)|
| Config       | python-dotenv       |

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Set your Gemini API key
#    Copy .env.example to .env and paste your key
cp .env.example .env   # then edit .env

# 3. (Optional) Generate sample lecture PDFs
pip install reportlab
python generate_samples.py

# 4. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501**.

### Configuring the Gemini API key

1. Copy `.env.example` to `.env`.
2. Paste your key after `GEMINI_API_KEY=`.
3. Restart the Streamlit app.

If no key is provided, StudyMate still works — it just shows the raw matching passages instead of an AI-generated answer.

## Architecture

```
PDF files
  │
  ▼
Text Extraction (pypdf)
  │
  ▼
Chunking (split pages into ~800-char pieces)
  │
  ▼
TF-IDF Indexing (pure Python, in-memory)
  │
  ▼
Query ──► Cosine Similarity Search ──► Top-k Passages
  │                                        │
  ▼                                        ▼
Gemini (optional)                  Raw passages (offline mode)
  │
  ▼
Answer + Source Citations
```

## Limitations

- **No OCR** — scanned PDFs (images of text) won't be extracted; the app warns you.
- **In-memory index** — the index lives in RAM and resets when you refresh the page. Fine for a few hundred pages, not for thousands.
- **Simple retrieval** — TF-IDF is keyword-based; it may miss semantically similar but differently-worded passages. A vector embedding model would do better, but adds complexity.
- **No persistent storage** — uploaded files and the index are lost on restart.
- **Single session** — designed for one user at a time.

## Mocked / Simplified Components

To keep the application simple and easy to run locally, the following components are mocked or simplified:
- **Database**: There is no external database. The TF-IDF index and extracted text live entirely in-memory and will reset when the app restarts.
- **Authentication**: There is no user login system. The app runs in a single-user mode locally.
- **Vector Embeddings**: Instead of using heavy embeddings (like OpenAI embeddings) and a vector database (like Pinecone or FAISS), retrieval is done locally using a lightweight, pure-Python TF-IDF implementation.

## Demo

You can demonstrate the full workflow in under 90 seconds:

1. **Start the app** (`streamlit run app.py`) — show the welcome screen.
2. **Upload PDFs** — drag the 3 sample PDFs from `sample_data/` into the sidebar.
3. **Process** — click "Process Documents", wait for the success message.
4. **Ask an answerable question** — *"What are the main principles of TQM?"* → show the AI answer and source citations.
5. **Ask an unanswerable question** — *"What is quantum computing?"* → show the "Not found" message.
6. **Show multiple sources** — *"What is the difference between casting and forging?"* → show answer pulling from multiple pages.

## Project Structure

```
StudyMate/
├── app.py                  # Streamlit application (UI + logic)
├── retrieval.py            # PDF extraction, chunking, TF-IDF search
├── generate_samples.py     # Script to create sample lecture PDFs
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment config
├── .gitignore
├── README.md
└── sample_data/
    ├── README.md           # Instructions for sample data
    ├── TQM_Lecture.pdf             # (generated)
    ├── Manufacturing_Processes.pdf # (generated)
    └── Operations_Research.pdf     # (generated)
```
