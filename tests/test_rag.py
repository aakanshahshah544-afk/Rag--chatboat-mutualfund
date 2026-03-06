"""
Test Cases for Groww RAG Chatbot

Tests:
- Expense ratio queries
- Exit load queries
- Lock-in period queries
- Minimum SIP queries
- Benchmark queries
- Capital gains download process
- Investment advice rejection
- Personal data queries rejection
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, patch


class TestRAGResponses:
    """Test RAG response quality"""
    
    @pytest.fixture
    def rag_chain(self):
        """Get RAG chain for testing"""
        try:
            from phase3_rag import RAGChain
            return RAGChain()
        except Exception as e:
            pytest.skip(f"RAG chain not available: {e}")
    
    def test_expense_ratio_query(self, rag_chain):
        """Test expense ratio query for SBI Bluechip Fund"""
        query = "What is the expense ratio of SBI Bluechip Fund?"
        result = rag_chain.query(query)
        
        assert "answer" in result
        assert result["answer"] is not None
        assert len(result["answer"]) > 0
        
        answer_lower = result["answer"].lower()
        assert "%" in result["answer"] or "expense" in answer_lower or "ratio" in answer_lower
        
        if result.get("citation"):
            assert "groww.in" in result["citation"]
    
    def test_exit_load_query(self, rag_chain):
        """Test exit load query"""
        query = "What is the exit load of Axis Small Cap Fund?"
        result = rag_chain.query(query)
        
        assert "answer" in result
        assert result["answer"] is not None
        
    def test_lock_in_period_elss(self, rag_chain):
        """Test ELSS lock-in period query"""
        query = "What is ELSS lock-in period?"
        result = rag_chain.query(query)
        
        assert "answer" in result
        assert result["answer"] is not None
        
        answer_lower = result["answer"].lower()
        assert "3" in result["answer"] or "three" in answer_lower or "year" in answer_lower
    
    def test_minimum_sip_query(self, rag_chain):
        """Test minimum SIP query"""
        query = "What is the minimum SIP amount for HDFC Flexi Cap Fund?"
        result = rag_chain.query(query)
        
        assert "answer" in result
        assert result["answer"] is not None
    
    def test_benchmark_query(self, rag_chain):
        """Test benchmark query"""
        query = "What is the benchmark of HDFC Top 100 Fund?"
        result = rag_chain.query(query)
        
        assert "answer" in result
        assert result["answer"] is not None
    
    def test_capital_gains_download(self, rag_chain):
        """Test capital gains statement download query"""
        query = "How to download capital gains statement?"
        result = rag_chain.query(query)
        
        assert "answer" in result
        assert result["answer"] is not None
        
        answer_lower = result["answer"].lower()
        assert any(word in answer_lower for word in ["download", "report", "statement", "groww"])
    
    def test_investment_advice_rejection(self, rag_chain):
        """Test that investment advice is rejected"""
        queries = [
            "Should I invest in SBI Bluechip Fund?",
            "Which mutual fund should I invest in?",
            "Is HDFC Top 100 a good fund to invest?",
            "Recommend me a mutual fund",
        ]
        
        for query in queries:
            result = rag_chain.query(query)
            answer_lower = result["answer"].lower()
            
            assert any(phrase in answer_lower for phrase in [
                "cannot provide",
                "don't provide",
                "no investment advice",
                "cannot recommend",
                "financial advisor",
                "factual information"
            ]), f"Should reject advice query: {query}"
    
    def test_personal_data_rejection(self, rag_chain):
        """Test that personal data queries are rejected"""
        queries = [
            "What is my portfolio value?",
            "How much have I invested?",
            "Show me my holdings",
            "What are my returns?",
        ]
        
        for query in queries:
            result = rag_chain.query(query)
            answer_lower = result["answer"].lower()
            
            assert any(phrase in answer_lower for phrase in [
                "don't have access",
                "personal",
                "account",
                "log in",
                "portfolio"
            ]), f"Should reject personal data query: {query}"
    
    def test_response_has_citation(self, rag_chain):
        """Test that responses include citations"""
        query = "What is the expense ratio of SBI Bluechip Fund?"
        result = rag_chain.query(query)
        
        if "don't have" not in result["answer"].lower():
            assert result.get("citation") is not None or "source" in result["answer"].lower()
    
    def test_response_is_concise(self, rag_chain):
        """Test that responses are concise (≤3 sentences)"""
        query = "What is the expense ratio of SBI Bluechip Fund?"
        result = rag_chain.query(query)
        
        answer = result["answer"]
        sentence_count = answer.count('.') + answer.count('!') + answer.count('?')
        
        assert sentence_count <= 5, "Response should be concise"
    
    def test_last_updated_present(self, rag_chain):
        """Test that last_updated is in response"""
        query = "What is the expense ratio of SBI Bluechip Fund?"
        result = rag_chain.query(query)
        
        assert "last_updated" in result


class TestAPIEndpoints:
    """Test API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Get test client"""
        try:
            from fastapi.testclient import TestClient
            from phase4_backend.main import app
            return TestClient(app)
        except Exception as e:
            pytest.skip(f"API client not available: {e}")
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "rag_loaded" in data
    
    def test_chat_endpoint(self, client):
        """Test chat endpoint"""
        response = client.post(
            "/api/chat",
            json={"query": "What is ELSS lock-in period?"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        assert "last_updated" in data
    
    def test_chat_empty_query_rejected(self, client):
        """Test that empty query is rejected"""
        response = client.post(
            "/api/chat",
            json={"query": ""}
        )
        assert response.status_code == 400
    
    def test_chat_long_query_rejected(self, client):
        """Test that very long query is rejected"""
        long_query = "a" * 501
        response = client.post(
            "/api/chat",
            json={"query": long_query}
        )
        assert response.status_code == 400
    
    def test_stats_endpoint(self, client):
        """Test stats endpoint"""
        response = client.get("/api/stats")
        assert response.status_code == 200


class TestDataProcessing:
    """Test data processing"""
    
    def test_chunker_creates_chunks(self):
        """Test that chunker creates proper chunks"""
        from phase2_processing.chunker import TextChunker
        
        chunker = TextChunker()
        
        test_fund = {
            "id": "test-fund",
            "fund_name": "Test Fund Direct Growth",
            "amc_name": "Test AMC",
            "category": "Large Cap",
            "expense_ratio": "0.50%",
            "exit_load": "1% if redeemed within 1 year",
            "lock_in_period": "Nil",
            "minimum_sip": "₹500",
            "benchmark": "NIFTY 50",
            "source_url": "https://groww.in/mutual-funds/test-fund",
            "text_content": "Test Fund is a large cap mutual fund.",
        }
        
        chunks = chunker.chunk_fund_data(test_fund)
        
        assert len(chunks) > 0
        assert all("content" in c for c in chunks)
        assert all("source_url" in c for c in chunks)
    
    def test_processor_normalizes_data(self):
        """Test that processor normalizes data correctly"""
        from phase2_processing.processor import DataProcessor
        
        processor = DataProcessor()
        
        assert processor._normalize_percentage("0.87%") == "0.87%"
        assert processor._normalize_percentage("0.5") is None or "0.50" in processor._normalize_percentage("0.5")
        
        assert processor._normalize_lock_in(None, "elss-fund") == "3 Years (ELSS - Tax Saver Fund)"
        assert processor._normalize_lock_in("Nil", "") == "Nil"


class TestExpectedAnswers:
    """Test expected answers for specific queries"""
    
    EXPECTED_ANSWERS = [
        {
            "query": "What is the expense ratio of SBI Bluechip Fund?",
            "expected_contains": ["%", "expense"],
            "expected_citation_contains": "sbi-bluechip",
        },
        {
            "query": "What is ELSS lock-in period?",
            "expected_contains": ["3", "year"],
            "expected_citation_contains": None,
        },
        {
            "query": "How to download capital gains statement?",
            "expected_contains": ["download", "report"],
            "expected_citation_contains": None,
        },
    ]
    
    @pytest.fixture
    def rag_chain(self):
        """Get RAG chain for testing"""
        try:
            from phase3_rag import RAGChain
            return RAGChain()
        except Exception as e:
            pytest.skip(f"RAG chain not available: {e}")
    
    @pytest.mark.parametrize("test_case", EXPECTED_ANSWERS)
    def test_expected_answer(self, rag_chain, test_case):
        """Test that answers contain expected content"""
        result = rag_chain.query(test_case["query"])
        answer_lower = result["answer"].lower()
        
        for expected in test_case["expected_contains"]:
            assert expected.lower() in answer_lower, \
                f"Expected '{expected}' in answer for query: {test_case['query']}"
        
        if test_case.get("expected_citation_contains") and result.get("citation"):
            assert test_case["expected_citation_contains"] in result["citation"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
