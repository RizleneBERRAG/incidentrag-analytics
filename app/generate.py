import os
from app.retrieve import Retriever


class Generator:

    def __init__(self):
        self.retriever = Retriever(top_k=5)

    def build_context(self, hits):
        """
        Construit le contexte à partir des chunks récupérés.
        """

        context_parts = []

        for h in hits:
            context_parts.append(
                f"""
SOURCE: {h.metadata.get('cert_id')}
TEXTE: {h.text}
"""
            )

        return "\n".join(context_parts)

    def generate_prompt(self, question: str, context: str) -> str:
        """
        Prompt RAG simple.
        """

        return f"""
Tu es un assistant expert en cybersécurité.

Réponds uniquement à partir du contexte fourni.

Si tu n'as pas assez d'informations, dis-le.

---

CONTEXTE:
{context}

---

QUESTION:
{question}

---

Réponse structurée et concise :
"""

    def call_llm(self, prompt: str) -> str:
        """
        Version simple (fallback sans API externe).
        """

        # ⚠️ ici tu peux brancher OpenAI / Mistral plus tard
        return "Réponse générée (LLM non connecté). Prompt utilisé:\n\n" + prompt[:800]

    def answer(self, question: str):
        """
        Pipeline complet RAG.
        """

        hits = self.retriever.search(question)

        context = self.build_context(hits)
        prompt = self.generate_prompt(question, context)

        answer = self.call_llm(prompt)

        sources = [
            {
                "cert_id": h.metadata.get("cert_id"),
                "url": h.metadata.get("url"),
                "score": h.score
            }
            for h in hits
        ]

        return {
            "question": question,
            "answer": answer,
            "sources": sources
        }


def test():
    gen = Generator()

    res = gen.answer(
        "Quels sont les principaux risques dans les avis CERT-FR ?"
    )

    print("\n=== RÉPONSE ===\n")
    print(res["answer"])

    print("\n=== SOURCES ===\n")
    for s in res["sources"]:
        print(s)


if __name__ == "__main__":
    test()