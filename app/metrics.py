import time
from dataclasses import dataclass


@dataclass
class TimingResult:
    retrieval_time: float
    generation_time: float


class Metrics:

    def __init__(self):
        self.logs = []

    def start_timer(self):
        return time.time()

    def end_timer(self, start):
        return time.time() - start

    def measure_retrieval(self, retriever, query: str):
        """
        Mesure latence + qualité retrieval.
        """

        start = self.start_timer()
        results = retriever.search(query)
        duration = self.end_timer(start)

        avg_score = (
            sum(r.score for r in results) / len(results)
            if results else 0
        )

        return {
            "latency_ms": round(duration * 1000, 2),
            "avg_score": round(avg_score, 3),
            "results_count": len(results)
        }

    def measure_generation(self, generator, query: str):
        """
        Mesure latence génération.
        """

        start = self.start_timer()
        result = generator.answer(query)
        duration = self.end_timer(start)

        return {
            "latency_ms": round(duration * 1000, 2),
            "sources_count": len(result.get("sources", []))
        }

    def full_evaluation(self, generator, queries: list[str]):
        """
        Benchmark simple du système RAG.
        """

        report = []

        for q in queries:

            start = self.start_timer()
            result = generator.answer(q)
            total_time = self.end_timer(start)

            report.append({
                "question": q,
                "total_latency_ms": round(total_time * 1000, 2),
                "sources": len(result.get("sources", []))
            })

        return report