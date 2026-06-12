from app.retrieve import Retriever


class Generator:
    """
    Classe principale RAG :
    - récupère les documents pertinents
    - construit le contexte
    - génère une réponse (ou fallback local)
    """

    def __init__(self):
        self.retriever = Retriever(top_k=5)

    def build_context(self, hits):
        """
        Construit un contexte propre et limité pour le LLM.
        """
        context_parts = []

        for i, h in enumerate(hits):
            text = (h.text or "").strip()

            # limite taille pour éviter explosion du prompt
            text = text[:800]

            context_parts.append(
                f"""
==============================
SOURCE {i + 1}
ID: {h.metadata.get('cert_id')}
PRODUIT: {h.metadata.get('product')}
SCORE: {round(h.score, 3)}

CONTENU:
{text}
==============================
"""
            )

        return "\n".join(context_parts)

    def generate_prompt(self, question: str, context: str) -> str:
        """
        Prompt optimisé pour RAG.
        """

        return f"""
Tu es un expert en cybersécurité travaillant sur des avis CERT-FR.

Tu dois répondre UNIQUEMENT à partir du contexte fourni.

Règles :
- Si l'information n'est pas dans le contexte, dis : "information non disponible dans le corpus"
- Réponse claire, structurée, professionnelle
- Pas d'invention

---

CONTEXTE :
{context}

---

QUESTION :
{question}

---

RÉPONSE :
"""

    def call_llm(self, prompt: str) -> str:
        """
        Version fallback (sans API externe).
        """

        return (
            "🧠 RÉPONSE (mode local)\n\n"
            "Je m'appuie uniquement sur les documents CERT-FR fournis.\n\n"
            "---\n\n"
            + prompt[:1200]
        )

    def answer(self, question: str):
        """
        Pipeline complet RAG :
        1. retrieval
        2. construction du contexte
        3. génération prompt
        4. réponse
        5. sources
        """

        hits = self.retriever.search(question)
        context = self.build_context(hits)
        prompt = self.generate_prompt(question, context)
        answer = self.call_llm(prompt)

        sources = [
            {
                "cert_id": h.metadata.get("cert_id"),
                "title": h.metadata.get("title"),
                "url": h.metadata.get("url"),
                "score": round(h.score, 3),
            }
            for h in hits
        ]

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
        }