"""
Phase 3: Embedding Generation and Management

- Load structured JSON
- Create embeddings using sentence-transformers
- Store in FAISS vector database
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np


class EmbeddingManager:
    """Manage embeddings for RAG"""
    
    BASE_DIR = Path(__file__).parent.parent / "data"
    STRUCTURED_DIR = BASE_DIR / "structured"
    EMBEDDINGS_DIR = BASE_DIR / "embeddings"
    
    MODEL_NAME = "all-MiniLM-L6-v2"
    
    def __init__(self, load_existing: bool = True):
        self.EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.index = None
        self.chunks = []
        self.chunk_lookup = {}
        
        if load_existing:
            self._try_load_existing()
    
    def _try_load_existing(self):
        """Try to load existing embeddings"""
        index_path_faiss = self.EMBEDDINGS_DIR / "faiss_index.faiss"
        index_path_pkl = self.EMBEDDINGS_DIR / "faiss_index.pkl"
        chunks_path = self.EMBEDDINGS_DIR / "chunks_metadata.json"
        
        if not chunks_path.exists():
            return
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
        
        self.chunk_lookup = {c["id"]: c for c in self.chunks}
        
        # Try FAISS format first
        if index_path_faiss.exists():
            try:
                import faiss
                self.index = faiss.read_index(str(index_path_faiss))
                print(f"[OK] Loaded existing embeddings from .faiss: {len(self.chunks)} chunks")
                return
            except Exception as e:
                print(f"Could not load .faiss index: {e}")
        
        # Fallback to pickle format
        if index_path_pkl.exists():
            try:
                import pickle
                with open(index_path_pkl, 'rb') as f:
                    self.index = pickle.load(f)
                print(f"[OK] Loaded existing embeddings from .pkl: {len(self.chunks)} chunks")
                # Optionally convert to faiss format
                try:
                    import faiss
                    faiss.write_index(self.index, str(index_path_faiss))
                    print("[OK] Converted index to .faiss format")
                except Exception as e:
                    print(f"Could not convert to .faiss: {e}")
            except Exception as e:
                print(f"Could not load .pkl index: {e}")
        
        if self.index is None:
            print("No valid index found. Will need to rebuild.")
    
    def _load_model(self):
        """Load sentence transformer model"""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Loading embedding model: {self.MODEL_NAME}...")
                self.model = SentenceTransformer(self.MODEL_NAME)
                print("[OK] Model loaded")
            except ImportError:
                raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
    
    def load_chunks(self) -> List[Dict]:
        """Load chunks from structured data"""
        chunks_path = self.STRUCTURED_DIR / "chunks.json"
        
        if not chunks_path.exists():
            raise FileNotFoundError(f"Chunks not found at {chunks_path}. Run processor first.")
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_embeddings(self, chunks: List[Dict]) -> np.ndarray:
        """Create embeddings for all chunks"""
        self._load_model()
        
        texts = [chunk["content"] for chunk in chunks]
        
        print(f"Creating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        return embeddings
    
    def build_faiss_index(self, embeddings: np.ndarray):
        """Build FAISS index from embeddings"""
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss-cpu not installed. Run: pip install faiss-cpu")
        
        dimension = embeddings.shape[1]
        
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings.astype('float32'))
        
        print(f"[OK] Built FAISS index with {self.index.ntotal} vectors")
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        import faiss
        
        index_path = self.EMBEDDINGS_DIR / "faiss_index.faiss"
        faiss.write_index(self.index, str(index_path))
        
        chunks_path = self.EMBEDDINGS_DIR / "chunks_metadata.json"
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Saved index to {index_path}")
        print(f"[OK] Saved metadata to {chunks_path}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar chunks"""
        if self.index is None:
            raise ValueError("No index loaded. Build or load index first.")
        
        self._load_model()
        
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        try:
            scores, indices = self.index.search(
                query_embedding.astype('float32'),
                top_k
            )
        except TypeError as e:
            if "missing" in str(e) and "positional arguments" in str(e):
                # Fallback for older FAISS versions that require pre-allocated arrays
                print(f"FAISS search error: {e}. Trying older API.")
                import numpy as np
                scores = np.zeros((query_embedding.shape[0], top_k), dtype='float32')
                indices = np.zeros((query_embedding.shape[0], top_k), dtype='int64')
                self.index.search(
                    query_embedding.astype('float32'),
                    top_k,
                    scores,
                    indices
                )
                scores, indices = scores, indices
            else:
                raise
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                chunk["score"] = float(score)
                chunk["rank"] = i + 1
                results.append(chunk)
        
        return results
    
    def get_embedding_stats(self) -> Dict:
        """Get statistics about embeddings"""
        return {
            "total_chunks": len(self.chunks),
            "index_size": self.index.ntotal if self.index else 0,
            "model_name": self.MODEL_NAME,
            "embeddings_dir": str(self.EMBEDDINGS_DIR),
        }
    
    def run(self) -> Dict:
        """Run complete embedding pipeline"""
        print("=" * 60)
        print("PHASE 3: Building Embeddings")
        print("=" * 60)
        
        self.chunks = self.load_chunks()
        print(f"Loaded {len(self.chunks)} chunks")
        
        self.chunk_lookup = {c["id"]: c for c in self.chunks}
        
        embeddings = self.create_embeddings(self.chunks)
        
        self.build_faiss_index(embeddings)
        
        self.save_index()
        
        return self.get_embedding_stats()


if __name__ == "__main__":
    manager = EmbeddingManager(load_existing=False)
    stats = manager.run()
    print(f"\nEmbedding Stats: {stats}")
