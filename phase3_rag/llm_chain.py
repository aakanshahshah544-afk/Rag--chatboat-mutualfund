"""
Phase 3: LLM Chain for RAG

Uses Groq API for answer generation.
- LLM must NOT answer from its own knowledge
- Must only answer from retrieved embeddings
- Single LLM call per query
- Returns ≤3 sentences with citation
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from .retriever import Retriever


load_dotenv()


class RAGChain:
    """RAG chain using Groq LLM"""
    
    SYSTEM_PROMPT = """You are a helpful assistant that answers questions about mutual funds ONLY using the provided context from Groww website.

STRICT RULES:
1. ONLY answer using information from the provided context
2. If the answer is not in the context, say "I don't have this information from Groww"
3. Keep answers concise - maximum 3 sentences
4. Always include the source URL in your response
5. NEVER provide investment advice or recommendations
6. NEVER say things like "you should invest" or "this is a good fund"
7. If asked for personal opinions or advice, politely refuse
8. If asked about personal data, refuse and explain you don't have access to user accounts
9. Format numbers clearly (use ₹ for currency, % for percentages)

RESPONSE FORMAT:
- Answer the factual question directly
- End with "Source: [URL]"
"""

    def __init__(self, retriever: Optional[Retriever] = None):
        self.retriever = retriever or Retriever()
        self.groq_client = None
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        self._init_groq()
    
    def _init_groq(self):
        """Initialize Groq client"""
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            print("Warning: GROQ_API_KEY not set in environment")
            return
        
        try:
            from groq import Groq
            self.groq_client = Groq(api_key=api_key)
        except ImportError:
            print("Warning: groq package not installed. Run: pip install groq")
    
    def _is_advice_query(self, query: str) -> bool:
        """Check if query is asking for investment advice"""
        advice_patterns = [
            r'should i (invest|buy|sell)',
            r'is it (good|bad|safe) to invest',
            r'recommend',
            r'best fund',
            r'which (fund|scheme) should',
            r'suggest',
            r'advice',
            r'opinion',
        ]
        
        query_lower = query.lower()
        for pattern in advice_patterns:
            if re.search(pattern, query_lower):
                return True
        return False
    
    def _is_personal_data_query(self, query: str) -> bool:
        """Check if query is asking for personal data"""
        personal_patterns = [
            r'my (portfolio|investments|holdings|balance)',
            r'how much (have i|did i)',
            r'my account',
            r'my transactions',
            r'my returns',
        ]
        
        query_lower = query.lower()
        for pattern in personal_patterns:
            if re.search(pattern, query_lower):
                return True
        return False
    
    def query(self, user_query: str) -> Dict:
        """Process a user query and return answer with citation"""
        
        if self._is_advice_query(user_query):
            return {
                "answer": "I can only provide factual information about mutual funds from Groww. I cannot provide investment advice or recommendations. Please consult a financial advisor for personalized guidance.",
                "citation": None,
                "last_updated": self.retriever.get_last_updated(),
                "query": user_query,
            }
        
        if self._is_personal_data_query(user_query):
            return {
                "answer": "I don't have access to your personal account data. This chatbot only provides general factual information about mutual funds available on Groww. Please log into your Groww account to view your portfolio.",
                "citation": None,
                "last_updated": self.retriever.get_last_updated(),
                "query": user_query,
            }
        
        context, sources = self.retriever.get_context_for_query(user_query, max_chunks=3)
        
        if not context:
            return {
                "answer": "I don't have information about this from Groww. Please check the Groww website directly.",
                "citation": "https://groww.in/mutual-funds",
                "last_updated": self.retriever.get_last_updated(),
                "query": user_query,
            }
        
        primary_citation = sources[0]["url"] if sources else "https://groww.in"
        
        if not self.groq_client:
            return self._fallback_response(user_query, context, sources)
        
        answer = self._call_llm(user_query, context)
        
        if primary_citation and primary_citation not in answer:
            if not answer.endswith('.'):
                answer += '.'
            answer += f"\nSource: {primary_citation}"
        
        return {
            "answer": answer,
            "citation": primary_citation,
            "last_updated": self.retriever.get_last_updated(),
            "query": user_query,
            "sources": sources,
        }
    
    def _call_llm(self, query: str, context: str) -> str:
        """Make a single LLM call to Groq"""
        
        user_message = f"""Context from Groww:
{context}

Question: {query}

Answer based ONLY on the context above. If the information is not in the context, say so."""

        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=300,
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"LLM call failed: {e}")
            return f"Error generating response: {str(e)}"
    
    def _fallback_response(self, query: str, context: str, sources: List[Dict]) -> Dict:
        """Generate response without LLM (for when Groq is unavailable)"""
        query_lower = query.lower()
        
        primary_citation = sources[0]["url"] if sources else "https://groww.in"
        
        for source in sources:
            content = source.get("content", context)
            
            if "expense ratio" in query_lower:
                match = re.search(r'expense ratio[:\s]*([0-9.]+%?)', content, re.IGNORECASE)
                if match:
                    fund_name = source.get("fund_name", "this fund")
                    return {
                        "answer": f"The expense ratio of {fund_name} is {match.group(1)}.\nSource: {primary_citation}",
                        "citation": primary_citation,
                        "last_updated": self.retriever.get_last_updated(),
                        "query": query,
                    }
            
            if "exit load" in query_lower:
                match = re.search(r'exit load[:\s]*([^\n.]+)', content, re.IGNORECASE)
                if match:
                    fund_name = source.get("fund_name", "this fund")
                    return {
                        "answer": f"The exit load for {fund_name} is {match.group(1)}.\nSource: {primary_citation}",
                        "citation": primary_citation,
                        "last_updated": self.retriever.get_last_updated(),
                        "query": query,
                    }
            
            if "lock" in query_lower and ("in" in query_lower or "period" in query_lower):
                match = re.search(r'lock[- ]?in[:\s]*([^\n.]+)', content, re.IGNORECASE)
                if match:
                    return {
                        "answer": f"{match.group(1)}.\nSource: {primary_citation}",
                        "citation": primary_citation,
                        "last_updated": self.retriever.get_last_updated(),
                        "query": query,
                    }
            
            if "minimum" in query_lower and "sip" in query_lower:
                match = re.search(r'minimum sip[:\s]*(₹?[0-9,]+)', content, re.IGNORECASE)
                if match:
                    fund_name = source.get("fund_name", "this fund")
                    return {
                        "answer": f"The minimum SIP amount for {fund_name} is {match.group(1)}.\nSource: {primary_citation}",
                        "citation": primary_citation,
                        "last_updated": self.retriever.get_last_updated(),
                        "query": query,
                    }
            
            if "benchmark" in query_lower:
                match = re.search(r'benchmark[:\s]*([^\n.]+)', content, re.IGNORECASE)
                if match:
                    fund_name = source.get("fund_name", "this fund")
                    return {
                        "answer": f"The benchmark for {fund_name} is {match.group(1)}.\nSource: {primary_citation}",
                        "citation": primary_citation,
                        "last_updated": self.retriever.get_last_updated(),
                        "query": query,
                    }
            
            if "capital gain" in query_lower and "download" in query_lower:
                return {
                    "answer": "To download your capital gains statement from Groww: 1) Log in to your Groww account, 2) Go to Reports section, 3) Select Capital Gains Statement, 4) Choose the financial year, 5) Click Download.\nSource: https://groww.in/help/tax/capital-gains",
                    "citation": "https://groww.in/help/tax/capital-gains",
                    "last_updated": self.retriever.get_last_updated(),
                    "query": query,
                }
        
        snippet = context[:200] if context else "Information not available"
        return {
            "answer": f"Based on Groww data: {snippet}...\nSource: {primary_citation}",
            "citation": primary_citation,
            "last_updated": self.retriever.get_last_updated(),
            "query": query,
        }


if __name__ == "__main__":
    rag = RAGChain()
    
    test_queries = [
        "What is the expense ratio of SBI Bluechip Fund?",
        "What is ELSS lock-in period?",
        "What is exit load of Axis Small Cap Fund?",
        "How to download capital gains statement?",
        "Should I invest in mutual funds?",
        "What is my portfolio value?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print("-" * 60)
        result = rag.query(query)
        print(f"Answer: {result['answer']}")
        print(f"Citation: {result.get('citation')}")
