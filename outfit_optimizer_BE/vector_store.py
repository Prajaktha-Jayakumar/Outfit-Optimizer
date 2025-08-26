import faiss
import numpy as np
import os
import json
from typing import Dict, Any, List, Tuple

INDEX_PATH = "data/wardrobe.index"
META_PATH = "data/wardrobe_meta.json"


def _ensure_paths():
    os.makedirs("data", exist_ok=True)


def load_index(d: int) -> faiss.Index:
    _ensure_paths()
    if os.path.exists(INDEX_PATH):
        return faiss.read_index(INDEX_PATH)
    # L2 index (vectors are already normalized); you can also use IndexFlatIP
    return faiss.IndexFlatL2(d)


def save_index(index: faiss.Index) -> None:
    faiss.write_index(index, INDEX_PATH)


def load_metadata() -> Dict[str, Any]:
    _ensure_paths()
    if os.path.exists(META_PATH):
        with open(META_PATH, "r") as f:
            return json.load(f)
    return {}


def save_metadata(meta: Dict[str, Any]) -> None:
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)


def add_item(embedding: np.ndarray, record: Dict[str, Any]) -> int:
    index = load_index(len(embedding))
    meta = load_metadata()
    
    # Make 2D float32 array
    vec = embedding.reshape(1, -1).astype("float32")
    idx = len(meta)  # simple incremental id
    
    index.add(vec)
    meta[str(idx)] = record
    
    save_index(index)
    save_metadata(meta)
    
    return idx


def search_similar(embedding: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
    index = load_index(len(embedding))
    if index.ntotal == 0:
        return []
    
    vec = embedding.reshape(1, -1).astype("float32")
    distances, ids = index.search(vec, k)
    
    return [(int(i), float(d)) for i, d in zip(ids[0], distances[0]) if i != -1]