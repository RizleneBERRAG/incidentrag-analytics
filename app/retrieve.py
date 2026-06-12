from app.store import ChromaStore
from sentence_transformers import SentenceTransformer


class Retriever:

    def __init__(self,
                 model_name="sentence-transformers/all-MiniLM-L6-v2",
                 top_k=5):

        self.model = SentenceTransformer(model_name)
        self.top_k = top_k

        self.store = ChromaStore()
        self.store.ensure_collection()

    def embed_query(self, query: str):
        """
        Transforme une question en vecteur.
        """
        return self.model.encode(query).tolist()

    def search(self, query: str):
        """
        Recherche les chunks les plus pertinents.
        """

        query_vector = self.embed_query(query)

        hits = self.store.search(
            query_vector=query_vector,
            top_k=self.top_k
        )

        return hits


def test():
    retriever = Retriever()

    query = "Quels sont les produits les plus touchés par des vulnérabilités ?"

    results = retriever.search(query)

    print("\nRésultats :\n")

    for r in results:
        print(f"- SCORE: {r.score:.3f}")
        print(f"- TEXT: {r.text[:200]}...")
        print(f"- CERT: {r.metadata.get('cert_id')}")
        print("")


if __name__ == "__main__":
    test()