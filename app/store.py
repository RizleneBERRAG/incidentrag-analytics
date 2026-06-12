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
        self.client = chromadb.HttpClient(
            host=host,
            port=port
        )

        self.collection = None

    def ensure_collection(self, dim=None):
        """
        Crée ou récupère la collection Chroma.
        """

        self.collection = self.client.get_or_create_collection(
            name="rag_chunks"
        )
           
    def upsert(self, ids, vectors, texts, metadatas):
        """
        Ajoute ou met à jour des embeddings.
        """

        if self.collection is None:
            raise RuntimeError(
                "Collection non initialisée."
            )

        self.collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=texts,
            metadatas=metadatas
        )

    def search(self, query_vector, top_k=5):
        """
        Recherche les chunks les plus proches.
        """

        if self.collection is None:
            raise RuntimeError(
                "Collection non initialisée."
            )

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )

        hits = []

        for i in range(len(results["ids"][0])):

            distance = results["distances"][0][i]

            score = 1.0 - distance

            hits.append(
                Hit(
                    id=results["ids"][0][i],
                    text=results["documents"][0][i],
                    metadata=results["metadatas"][0][i],
                    score=score
                )
            )

        return hits