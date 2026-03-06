# Groww RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that answers factual mutual fund queries from Groww.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          GROWW RAG CHATBOT                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │   Phase 1   │───▶│   Phase 2   │───▶│   Phase 3   │                  │
│  │   Scraper   │    │  Processing │    │     RAG     │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
│         │                  │                  │                          │
│         ▼                  ▼                  ▼                          │
│    /data/raw/       /data/structured/   /data/embeddings/               │
│                                                                          │
│  ┌─────────────────────────────────────────────────────┐                │
│  │                    Phase 4                          │                │
│  │  ┌─────────────┐              ┌─────────────┐      │                │
│  │  │   FastAPI   │◀────────────▶│  Frontend   │      │                │
│  │  │   Backend   │              │   Chat UI   │      │                │
│  │  └─────────────┘              └─────────────┘      │                │
│  └─────────────────────────────────────────────────────┘                │
│                                                                          │
│  ┌─────────────┐                                                        │
│  │   Phase 5   │  Daily Scheduler - Re-scrapes & rebuilds embeddings   │
│  │  Scheduler  │                                                        │
│  └─────────────┘                                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
M1/
├── phase1_scraper/          # Web scraping module
│   ├── __init__.py
│   ├── scraper.py           # Main scraper logic
│   ├── fund_urls.py         # List of fund URLs to scrape
│   └── help_scraper.py      # Help page scraper
│
├── phase2_processing/       # Data processing module
│   ├── __init__.py
│   ├── processor.py         # Data cleaning & structuring
│   └── chunker.py           # Text chunking logic
│
├── phase3_rag/              # RAG implementation
│   ├── __init__.py
│   ├── embeddings.py        # Embedding generation
│   ├── retriever.py         # Vector similarity search
│   └── llm_chain.py         # Groq LLM integration
│
├── phase4_backend/          # Backend & Frontend
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── routes.py            # API routes
│   └── frontend/            # Static frontend files
│       ├── index.html
│       ├── styles.css
│       └── app.js
│
├── phase5_scheduler/        # Daily scheduler
│   ├── __init__.py
│   └── scheduler.py         # Scheduling logic
│
├── data/                    # Data storage
│   ├── raw/                 # Raw scraped HTML
│   ├── structured/          # Processed JSON
│   └── embeddings/          # FAISS index
│
├── tests/                   # Test cases
│   ├── __init__.py
│   └── test_rag.py
│
├── requirements.txt
├── .env.example
└── README.md
```

## Phases

### Phase 1: Scraping
- Scrapes mutual fund pages from Groww
- Extracts: Fund Name, AMC, Category, Expense Ratio, Exit Load, Lock-in Period, Riskometer, Benchmark, Min SIP, AUM, Fund Manager, Returns
- Scrapes help pages for ELSS, capital gains, etc.

### Phase 2: Processing
- Cleans HTML content
- Normalizes numbers
- Structures data into JSON
- Chunks by logical sections

### Phase 3: RAG
- Generates embeddings using sentence-transformers
- Stores in FAISS vector database
- Retrieves relevant chunks for queries
- Uses Groq LLM for answer generation

### Phase 4: Backend & Frontend
- FastAPI backend with single endpoint
- Single LLM call per query
- Returns answer + citation + last_updated
- Simple chat UI with example questions

### Phase 5: Scheduler
- Runs daily at configured time
- Re-scrapes all pages
- Updates structured JSON
- Rebuilds embeddings

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

3. Run initial scraping:
```bash
python -m phase1_scraper.scraper
```

4. Process data:
```bash
python -m phase2_processing.processor
```

5. Build embeddings:
```bash
python -m phase3_rag.embeddings
```

6. Start the server:
```bash
python -m phase4_backend.main
```

7. Open browser at http://localhost:8000

## API Endpoints

### POST /api/chat
```json
{
  "query": "What is the expense ratio of SBI Bluechip Fund?"
}
```

Response:
```json
{
  "answer": "The expense ratio of SBI Bluechip Fund (Direct Growth) is 0.87%.",
  "citation": "https://groww.in/mutual-funds/sbi-bluechip-fund-direct-growth",
  "last_updated": "2024-03-01T10:30:00Z"
}
```

## Disclaimer

Facts-only. No investment advice. This chatbot provides factual information scraped from Groww and does not provide any investment recommendations.
