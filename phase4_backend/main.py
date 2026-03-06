"""
Phase 4: FastAPI Backend

- Single API endpoint for chat
- Single LLM call per query
- Returns answer, citation, last_updated
- Serves static frontend
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from phase3_rag import RAGChain


app = FastAPI(
    title="Groww RAG Chatbot API",
    description="A RAG chatbot for answering factual mutual fund queries from Groww",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_chain: Optional[RAGChain] = None


class ChatRequest(BaseModel):
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the expense ratio of SBI Bluechip Fund?"
            }
        }


class ChatResponse(BaseModel):
    answer: str
    citation: Optional[str] = None
    last_updated: str
    query: str
    sources: Optional[List[dict]] = None


class HealthResponse(BaseModel):
    status: str
    rag_loaded: bool
    total_chunks: int
    last_updated: str


def get_rag_chain() -> RAGChain:
    """Get or initialize RAG chain (cached in memory)"""
    global rag_chain
    
    if rag_chain is None:
        print("Initializing RAG chain...")
        rag_chain = RAGChain()
        print("RAG chain initialized")
    
    return rag_chain


@app.on_event("startup")
async def startup_event():
    """Initialize RAG chain on startup"""
    try:
        get_rag_chain()
        print("[OK] RAG system ready")
    except Exception as e:
        print(f"Warning: Could not initialize RAG on startup: {e}")


@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return JSONResponse(
        content={"message": "Frontend not found. Use /api/chat endpoint directly."},
        status_code=200
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health"""
    try:
        chain = get_rag_chain()
        stats = chain.retriever.embedding_manager.get_embedding_stats()
        
        return HealthResponse(
            status="healthy",
            rag_loaded=True,
            total_chunks=stats.get("total_chunks", 0),
            last_updated=chain.retriever.get_last_updated()
        )
    except Exception as e:
        return HealthResponse(
            status=f"unhealthy: {str(e)}",
            rag_loaded=False,
            total_chunks=0,
            last_updated="Unknown"
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat query and return answer with citation.
    
    Single LLM call per query.
    Returns factual information only - no investment advice.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if len(request.query) > 500:
        raise HTTPException(status_code=400, detail="Query too long (max 500 characters)")
    
    try:
        chain = get_rag_chain()
        result = chain.query(request.query.strip())
        
        return ChatResponse(
            answer=result["answer"],
            citation=result.get("citation"),
            last_updated=result.get("last_updated", "Unknown"),
            query=result.get("query", request.query),
            sources=result.get("sources")
        )
    
    except Exception as e:
        print(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    try:
        chain = get_rag_chain()
        stats = chain.retriever.embedding_manager.get_embedding_stats()
        
        return {
            "total_chunks": stats.get("total_chunks", 0),
            "model_name": stats.get("model_name", "Unknown"),
            "last_updated": chain.retriever.get_last_updated(),
            "llm_model": chain.model,
        }
    except Exception as e:
        return {"error": str(e)}


FRONTEND_DIR = Path(__file__).parent / "frontend"


@app.get("/styles.css")
async def serve_css():
    """Serve CSS file"""
    css_path = FRONTEND_DIR / "styles.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS not found")


@app.get("/app.js")
async def serve_js():
    """Serve JavaScript file"""
    js_path = FRONTEND_DIR / "app.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JavaScript not found")


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
