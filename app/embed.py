from sentence_transformers import SentenceTransformer
import json
from pathlib import Path
from app.store import ChromaStore


CHUNKS_FILE = Path("corpus/chunks.jsonl")


class Embedder:

    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        return self.model.encode(texts).tolist()


def load_chunks(path: Path):
    chunks = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    return chunks


def main():

    print("Chargement des chunks...")
    chunks = load_chunks(CHUNKS_FILE)

    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    print("Génération embeddings...")
    embedder = Embedder()
    vectors = embedder.encode(texts)

    print("Stockage dans Chroma...")
    store = ChromaStore()
    store.ensure_collection()
    store.upsert(ids, vectors, texts, metadatas)

    print("Indexation terminée.")


if __name__ == "__main__":
    main()