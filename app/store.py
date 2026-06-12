import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import chromadb
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Hit:
    """
    Représente un résultat retourné par Chroma.
    """
    id: str
    text: str
    metadata: Dict[str, Any]
    score: Optional[float]


class ChromaStore:
    """
    Gestion du vector store Chroma.

    Le store est utilisé par :
    - app/embed.py pour indexer les chunks ;
    - app/retrieve.py pour rechercher les chunks pertinents ;
    - app/generate.py pour construire une réponse avec sources.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_name: Optional[str] = None
    ):
        self.host = host or os.getenv("CHROMA_HOST", "localhost")
        self.port = int(port or os.getenv("CHROMA_PORT", "8001"))
        self.collection_name = collection_name or os.getenv("CHROMA_COLLECTION", "rag_chunks")

        self.client = chromadb.HttpClient(
            host=self.host,
            port=self.port
        )

        self.collection = None

    def ensure_collection(self):
        """
        Crée ou récupère la collection Chroma.
        """
        if self.collection is None:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

        return self.collection

    def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> None:
        """
        Ajoute ou met à jour les embeddings dans Chroma.
        """
        if not (len(ids) == len(vectors) == len(texts) == len(metadatas)):
            raise ValueError(
                "Incohérence entre ids, vectors, texts et metadatas."
            )

        collection = self.ensure_collection()

        clean_metadatas = [
            self.clean_metadata(metadata)
            for metadata in metadatas
        ]

        total = len(ids)

        for start in range(0, total, batch_size):
            end = start + batch_size

            collection.upsert(
                ids=ids[start:end],
                embeddings=vectors[start:end],
                documents=texts[start:end],
                metadatas=clean_metadatas[start:end]
            )

            print(f"Indexation Chroma : {min(end, total)}/{total} chunks")

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Hit]:
        """
        Recherche les chunks les plus proches d'une question.
        """
        collection = self.ensure_collection()

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )

        hits = []

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for index, chunk_id in enumerate(ids):
            distance = distances[index] if index < len(distances) else None
            score = self.distance_to_score(distance)

            hits.append(
                Hit(
                    id=chunk_id,
                    text=documents[index] if index < len(documents) else "",
                    metadata=metadatas[index] if index < len(metadatas) else {},
                    score=score
                )
            )

        return hits

    def clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chroma accepte seulement des métadonnées simples :
        str, int, float, bool ou None.

        Cette méthode transforme les listes/dictionnaires en JSON texte.
        """
        clean = {}

        for key, value in (metadata or {}).items():
            if value is None:
                clean[key] = ""
            elif isinstance(value, (str, int, float, bool)):
                clean[key] = value
            else:
                clean[key] = json.dumps(value, ensure_ascii=False)

        return clean

    def distance_to_score(self, distance: Optional[float]) -> Optional[float]:
        """
        Convertit une distance Chroma en score lisible.

        Plus le score est proche de 1, plus le chunk est pertinent.
        """
        if distance is None:
            return None

        try:
            distance = float(distance)
        except (TypeError, ValueError):
            return None

        if distance <= 1:
            score = 1 - distance
        else:
            score = 1 / (1 + distance)

        return round(max(0.0, min(1.0, score)), 4)