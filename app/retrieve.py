import os
from typing import List, Optional

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from app.store import ChromaStore, Hit


load_dotenv()


class Retriever:
    """
    Recherche les chunks les plus pertinents dans Chroma à partir d'une question.

    Étapes :
    1. encoder la question avec le même modèle que pour les chunks ;
    2. interroger Chroma ;
    3. retourner les meilleurs résultats avec score + métadonnées.
    """

    def __init__(
        self,
        top_k: Optional[int] = None,
        embedding_model_name: Optional[str] = None,
        store: Optional[ChromaStore] = None
    ):
        self.top_k = int(top_k or os.getenv("TOP_K", "5"))
        self.embedding_model_name = embedding_model_name or os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        self.model = SentenceTransformer(self.embedding_model_name)
        self.store = store or ChromaStore()

    def search(self, question: str, top_k: Optional[int] = None) -> List[Hit]:
        """
        Recherche les chunks les plus proches de la question.
        """
        question = (question or "").strip()

        if not question:
            return []

        query_vector = self.encode_question(question)
        limit = int(top_k or self.top_k)

        return self.store.search(
            query_vector=query_vector,
            top_k=limit
        )

    def encode_question(self, question: str) -> List[float]:
        """
        Transforme la question en vecteur.
        """
        embedding = self.model.encode(
            question,
            normalize_embeddings=True
        )

        if hasattr(embedding, "tolist"):
            return embedding.tolist()

        return list(embedding)


def test():
    retriever = Retriever()

    question = "Quelles vulnérabilités concernent Microsoft Windows ?"
    hits = retriever.search(question)

    print("\n=== QUESTION ===")
    print(question)

    print("\n=== RÉSULTATS ===")
    for index, hit in enumerate(hits, start=1):
        print(f"\n--- Résultat {index} ---")
        print(f"ID : {hit.id}")
        print(f"Score : {hit.score}")
        print(f"Titre : {hit.metadata.get('title')}")
        print(f"Produit : {hit.metadata.get('product')}")
        print(f"URL : {hit.metadata.get('url')}")
        print(f"Extrait : {hit.text[:300]}...")


if __name__ == "__main__":
    test()