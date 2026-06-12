import os
import re
from typing import List

from dotenv import load_dotenv

from app.retrieve import Retriever


load_dotenv()


class Generator:
    """
    Génère une réponse RAG à partir des chunks retrouvés.

    Cette version fonctionne sans API LLM externe :
    - elle utilise le retriever pour récupérer les passages pertinents ;
    - elle extrait les phrases les plus utiles ;
    - elle construit une réponse structurée avec sources.

    Cela permet d'avoir un MVP démontrable même sans clé API.
    """

    def __init__(self):
        self.top_k = int(os.getenv("TOP_K", "5"))
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.55"))
        self.retriever = Retriever(top_k=self.top_k)

    def answer(self, question: str) -> dict:
        """
        Pipeline complet :
        question -> retrieval Chroma -> réponse synthétique -> sources.
        """
        question = question.strip()

        if not question:
            return {
                "question": question,
                "answer": "La question est vide. Merci de poser une question sur le corpus CERT-FR.",
                "sources": []
            }

        hits = self.retriever.search(question)

        if not hits:
            return {
                "question": question,
                "answer": (
                    "Je n'ai pas trouvé de passage pertinent dans le corpus CERT-FR "
                    "pour répondre à cette question."
                ),
                "sources": []
            }

        filtered_hits = self.filter_hits(hits)

        answer_text = self.build_answer(question, filtered_hits)
        sources = self.build_sources(filtered_hits)

        return {
            "question": question,
            "answer": answer_text,
            "sources": sources
        }

    def filter_hits(self, hits: list) -> list:
        """
        Filtre les résultats selon le score de similarité.

        Si aucun résultat ne dépasse le seuil, on garde quand même les meilleurs
        résultats pour éviter une réponse vide pendant la démonstration.
        """
        filtered = []

        for hit in hits:
            if hit.score is None:
                filtered.append(hit)
            elif hit.score >= self.similarity_threshold:
                filtered.append(hit)

        if filtered:
            return filtered

        return hits[: min(3, len(hits))]

    def build_answer(self, question: str, hits: list) -> str:
        """
        Construit une réponse claire à partir des passages récupérés.
        """
        if not hits:
            return (
                "Les sources retrouvées ne sont pas assez pertinentes pour répondre "
                "correctement à cette question."
            )

        lines = [
            "D'après les avis CERT-FR retrouvés dans le corpus, voici les éléments pertinents :",
            ""
        ]

        for index, hit in enumerate(hits, start=1):
            metadata = hit.metadata or {}

            cert_id = metadata.get("cert_id", "Source CERT-FR")
            title = metadata.get("title", "Avis CERT-FR")
            product = metadata.get("product", "")
            date = metadata.get("date", "")
            systems = metadata.get("systems", "")

            excerpt = self.extract_relevant_excerpt(hit.text, question)

            source_title = f"{cert_id} — {title}"

            if date:
                source_title += f" ({date})"

            lines.append(f"{index}. {source_title}")

            if product:
                lines.append(f"   Produit concerné : {product}")

            if systems:
                lines.append(f"   Systèmes affectés : {self.shorten_text(systems, 220)}")

            lines.append(f"   Information utile : {excerpt}")
            lines.append("")

        lines.append(
            "Cette réponse est basée uniquement sur les passages récupérés dans le corpus. "
            "Les sources complètes sont retournées dans le champ `sources` de la réponse API."
        )

        return "\n".join(lines)

    def build_sources(self, hits: list) -> list:
        """
        Prépare les sources retournées par l'API.
        """
        sources = []

        for hit in hits:
            metadata = hit.metadata or {}

            sources.append({
                "id": hit.id,
                "cert_id": metadata.get("cert_id"),
                "title": metadata.get("title"),
                "date": metadata.get("date"),
                "product": metadata.get("product"),
                "url": metadata.get("url"),
                "score": round(hit.score, 4) if isinstance(hit.score, (int, float)) else hit.score,
                "excerpt": self.shorten_text(hit.text, 350)
            })

        return sources

    def extract_relevant_excerpt(self, text: str, question: str, max_sentences: int = 2) -> str:
        """
        Extrait les phrases les plus proches de la question.
        """
        clean = self.clean_text(text)
        sentences = self.split_sentences(clean)

        if not sentences:
            return self.shorten_text(clean, 350)

        question_terms = self.extract_question_terms(question)

        scored_sentences = []

        for sentence in sentences:
            score = self.score_sentence(sentence, question_terms)
            scored_sentences.append((score, sentence))

        scored_sentences.sort(key=lambda item: item[0], reverse=True)

        best_sentences = [
            sentence
            for score, sentence in scored_sentences
            if score > 0
        ][:max_sentences]

        if not best_sentences:
            best_sentences = sentences[:max_sentences]

        excerpt = " ".join(best_sentences)
        return self.shorten_text(excerpt, 450)

    def extract_question_terms(self, question: str) -> set:
        """
        Récupère les mots importants de la question.
        """
        stopwords = {
            "dans", "avec", "pour", "quoi", "quel", "quelle", "quels", "quelles",
            "sont", "est", "des", "les", "une", "un", "sur", "par", "qui",
            "que", "dont", "aux", "de", "du", "la", "le", "et", "ou", "en",
            "au", "ce", "ces", "ses", "plus", "moins", "principaux", "principales"
        }

        words = re.findall(r"[a-zA-ZÀ-ÿ0-9_.-]+", question.lower())

        return {
            word
            for word in words
            if len(word) >= 4 and word not in stopwords
        }

    def score_sentence(self, sentence: str, question_terms: set) -> int:
        """
        Score simple selon les mots de la question présents dans la phrase.
        """
        sentence_lower = sentence.lower()
        return sum(1 for term in question_terms if term in sentence_lower)

    def split_sentences(self, text: str) -> List[str]:
        """
        Découpe un texte en phrases simples.
        """
        sentences = re.split(r"(?<=[.!?])\s+", text)

        return [
            sentence.strip()
            for sentence in sentences
            if len(sentence.strip()) > 40
        ]

    def clean_text(self, text: str) -> str:
        """
        Nettoie les espaces.
        """
        text = text or ""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def shorten_text(self, text: str, max_length: int = 300) -> str:
        """
        Raccourcit un texte proprement.
        """
        text = self.clean_text(text)

        if len(text) <= max_length:
            return text

        return text[:max_length].rstrip() + "..."


def test():
    generator = Generator()

    result = generator.answer(
        "Quelles vulnérabilités concernent Microsoft Windows ?"
    )

    print("\n=== QUESTION ===\n")
    print(result["question"])

    print("\n=== RÉPONSE ===\n")
    print(result["answer"])

    print("\n=== SOURCES ===\n")
    for source in result["sources"]:
        print(source)


if __name__ == "__main__":
    test()
