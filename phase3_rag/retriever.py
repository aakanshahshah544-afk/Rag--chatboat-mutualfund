"""
Phase 3: Retriever for RAG

Handles semantic search and retrieval of relevant chunks.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .embeddings import EmbeddingManager


class Retriever:
    """Retrieve relevant chunks for queries"""
    
    BASE_DIR = Path(__file__).parent.parent / "data"
    STRUCTURED_DIR = BASE_DIR / "structured"
    
    def __init__(self, embedding_manager: Optional[EmbeddingManager] = None):
        self.embedding_manager = embedding_manager or EmbeddingManager(load_existing=True)
        self._load_structured_data()
    
    def _load_structured_data(self):
        """Load structured fund data for additional context"""
        funds_path = self.STRUCTURED_DIR / "funds.json"
        
        if funds_path.exists():
            with open(funds_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.funds = {f["id"]: f for f in data.get("funds", [])}
                self.help_pages = {p["id"]: p for p in data.get("help_pages", [])}
                self.metadata = data.get("metadata", {})
        else:
            self.funds = {}
            self.help_pages = {}
            self.metadata = {}
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant chunks for a query"""
        query_lower = query.lower()
        
        fund_keywords = self._extract_fund_keywords(query_lower)
        
        results = self.embedding_manager.search(query, top_k=max(20, top_k * 10))
        
        if fund_keywords:
            results = self._boost_matching_funds(results, fund_keywords)
        
        results = results[:top_k]
        
        for result in results:
            result["last_updated"] = self.metadata.get("last_updated", "Unknown")
        
        return results
    
    def _extract_fund_keywords(self, query: str) -> List[str]:
        """Extract fund name keywords from query"""
        keywords = []
        
        amc_names = ['sbi', 'hdfc', 'axis', 'icici', 'kotak', 'prudential']
        fund_types = ['bluechip', 'small cap', 'smallcap', 'mid cap', 'midcap', 
                      'flexi cap', 'flexicap', 'elss', 'tax saver', 'index',
                      'balanced', 'hybrid', 'focused', 'value']
        
        for amc in amc_names:
            if amc in query:
                keywords.append(amc)
        
        for fund_type in fund_types:
            if fund_type in query:
                keywords.append(fund_type)
        
        return keywords
    
    def _boost_matching_funds(self, results: List[Dict], keywords: List[str]) -> List[Dict]:
        """Boost results that match fund keywords"""
        for result in results:
            # Some chunks may not have fund_name/content set (or may be None)
            fund_name = (result.get("fund_name") or "").lower()
            content = (result.get("content") or "").lower()
            
            boost = 0
            for keyword in keywords:
                if keyword in fund_name:
                    boost += 0.2
                elif keyword in content:
                    boost += 0.1
            
            result["score"] = result.get("score", 0) + boost
        
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return results
    
    def get_context_for_query(self, query: str, max_chunks: int = 3) -> Tuple[str, List[Dict]]:
        """Get formatted context for LLM query"""
        results = self.retrieve(query, top_k=max_chunks)
        
        if not results:
            return "", []
        
        context_parts = []
        sources = []
        
        seen_content = set()
        
        for result in results:
            content = result.get("content", "")
            
            content_hash = hash(content[:100])
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)
            
            context_parts.append(f"[Source: {result.get('source_url', 'Groww')}]\n{content}")
            
            sources.append({
                "url": result.get("source_url", ""),
                "fund_name": result.get("fund_name", ""),
                "chunk_type": result.get("chunk_type", ""),
                "score": result.get("score", 0),
            })
        
        context = "\n\n---\n\n".join(context_parts)
        
        return context, sources
    
    def get_last_updated(self) -> str:
        """Get last updated timestamp"""
        return self.metadata.get("last_updated", "Unknown")
    
    def reload_data(self):
        """Reload structured data and embeddings"""
        self._load_structured_data()
        self.embedding_manager = EmbeddingManager(load_existing=True)


if __name__ == "__main__":
    retriever = Retriever()
    
    test_queries = [
        "What is the expense ratio of SBI Bluechip Fund?",
        "What is ELSS lock-in period?",
        "How to download capital gains statement?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        results = retriever.retrieve(query, top_k=3)
        for r in results:
            print(f"  Score: {r['score']:.3f} | {r.get('fund_name', r.get('category', 'N/A'))}")
            print(f"  Content: {r['content'][:100]}...")
            print()
