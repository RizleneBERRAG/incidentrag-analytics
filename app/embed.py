import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from app.store import ChromaStore


load_dotenv()


class Embedder:
    """
    Génère les embeddings des chunks et les stocke dans Chroma.

    Entrée :
    - corpus/chunks.jsonl

    Sortie :
    - collection Chroma contenant les chunks vectorisés
    """

    def __init__(self):
        self.chunks_path = Path(os.getenv("CHUNKS_PATH", "corpus/chunks.jsonl"))
        self.embedding_model_name = os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))

        self.model = SentenceTransformer(self.embedding_model_name)
        self.store = ChromaStore()

    def run(self) -> None:
        """
        Lance l'indexation complète du corpus.
        """
        print("Démarrage de l'indexation des chunks...")

        chunks = self.load_chunks()

        if not chunks:
            print("Aucun chunk trouvé. Vérifie que corpus/chunks.jsonl existe.")
            return

        print(f"Chunks chargés : {len(chunks)}")
        print(f"Modèle d'embedding : {self.embedding_model_name}")

        ids, texts, metadatas = self.prepare_chunks(chunks)

        total = len(texts)

        for start in range(0, total, self.batch_size):
            end = start + self.batch_size

            batch_ids = ids[start:end]
            batch_texts = texts[start:end]
            batch_metadatas = metadatas[start:end]

            vectors = self.encode_texts(batch_texts)

            self.store.upsert(
                ids=batch_ids,
                vectors=vectors,
                texts=batch_texts,
                metadatas=batch_metadatas,
                batch_size=self.batch_size
            )

            print(f"Embeddings générés : {min(end, total)}/{total}")

        print("Indexation terminée avec succès.")

    def load_chunks(self) -> List[Dict[str, Any]]:
        """
        Charge les chunks depuis un fichier JSONL.
        """
        if not self.chunks_path.exists():
            raise FileNotFoundError(
                f"Fichier introuvable : {self.chunks_path}. "
                "Lance d'abord : python app/ingest.py"
            )

        chunks = []

        with self.chunks_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Erreur JSON dans {self.chunks_path}, ligne {line_number}"
                    ) from error

        return chunks

    def prepare_chunks(
        self,
        chunks: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
        """
        Prépare les ids, textes et métadonnées pour Chroma.

        Le code est volontairement tolérant :
        - il accepte id, chunk_id ou cert_id comme identifiant ;
        - il accepte text ou content comme contenu ;
        - il reconstruit les métadonnées si elles sont à plat.
        """
        ids = []
        texts = []
        metadatas = []

        for index, chunk in enumerate(chunks):
            chunk_id = self.get_chunk_id(chunk, index)
            text = self.get_chunk_text(chunk)

            if not text:
                continue

            metadata = self.get_metadata(chunk)

            ids.append(chunk_id)
            texts.append(text)
            metadatas.append(metadata)

        if not ids:
            raise ValueError(
                "Aucun chunk exploitable trouvé dans le fichier JSONL."
            )

        return ids, texts, metadatas

    def get_chunk_id(self, chunk: Dict[str, Any], index: int) -> str:
        """
        Récupère ou génère un identifiant unique.
        """
        chunk_id = (
            chunk.get("id")
            or chunk.get("chunk_id")
            or chunk.get("cert_id")
            or f"chunk-{index}"
        )

        return str(chunk_id)

    def get_chunk_text(self, chunk: Dict[str, Any]) -> str:
        """
        Récupère le texte du chunk.
        """
        text = chunk.get("text") or chunk.get("content") or ""
        return str(text).strip()

    def get_metadata(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère les métadonnées du chunk.
        """
        metadata = chunk.get("metadata")

        if isinstance(metadata, dict):
            clean_metadata = metadata.copy()
        else:
            clean_metadata = {}

        for key, value in chunk.items():
            if key not in {"text", "content", "metadata"}:
                clean_metadata.setdefault(key, value)

        return clean_metadata

    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Transforme une liste de textes en vecteurs.
        """
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()

        return [list(vector) for vector in embeddings]


def main():
    embedder = Embedder()
    embedder.run()

    print("DEBUG IDS:", ids[:3])
    print("DEBUG VECTORS:", len(vectors))

if __name__ == "__main__":
    main()