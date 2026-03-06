import pickle
import faiss
from pathlib import Path

# Load the old pickle index
index_path_pkl = Path("data/embeddings/faiss_index.pkl")
index_path_faiss = Path("data/embeddings/faiss_index.faiss")

if index_path_pkl.exists():
    with open(index_path_pkl, 'rb') as f:
        index = pickle.load(f)
    
    # Save as faiss format
    faiss.write_index(index, str(index_path_faiss))
    print("Converted index to .faiss format")
else:
    print("No pickle index found")