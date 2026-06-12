from dataclasses import dataclass
import chromadb


@dataclass
class Hit:
    id: str
    text: str
    metadata: dict
    score: float


class ChromaStore:
    def __init__(self, host="localhost", port=8001):
        self.client = chromadb.PersistentClient(path="chroma_db")
        self.collection = None

    def ensure_collection(self):
        self.collection = self.client.get_or_create_collection(
            name="rag_chunks"
        )

    def upsert(self, ids, vectors, texts, metadatas):
        if self.collection is None:
            self.ensure_collection()

        if not (len(ids) == len(vectors) == len(texts)):
            raise ValueError("Incohérence ids/vectors/texts")

        self.collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=texts,
            metadatas=metadatas
        )

    def search(self, query_vector, top_k=5):
        if self.collection is None:
            self.ensure_collection()

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        hits = []

        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        if not ids:
            return []

        for i in range(len(ids)):
            score = 1.0 - dists[i]

            hits.append(
                Hit(
                    id=ids[i],
                    text=docs[i],
                    metadata=metas[i],
                    score=score
                )
            )

        return hits