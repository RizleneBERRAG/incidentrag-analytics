from collections import Counter
from pathlib import Path
import json


CHUNKS_FILE = Path("corpus/chunks.jsonl")


def load_chunks():
    if not CHUNKS_FILE.exists():
        print("chunks.jsonl introuvable")
        return []

    chunks = []

    with CHUNKS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    return chunks


def analyze_trends(chunks):
    product_counter = Counter()
    risk_counter = Counter()

    for chunk in chunks:
        meta = chunk.get("metadata", {})

        product = meta.get("product") or "unknown"
        risks = meta.get("risks") or ""

        product_counter[product] += 1

        if risks:
            for r in risks.split(","):
                risk_counter[r.strip().lower()] += 1

    return {
        "top_products": product_counter.most_common(10),
        "top_risks": risk_counter.most_common(10),
    }


def print_trends(trends):
    print("\n=== TENDANCES CORPUS CERT-FR ===\n")

    print("Top produits :")
    for p, c in trends["top_products"]:
        print(f"- {p}: {c}")

    print("\nTop risques :")
    for r, c in trends["top_risks"]:
        print(f"- {r}: {c}")


def main():
    chunks = load_chunks()

    if not chunks:
        return

    trends = analyze_trends(chunks)
    print_trends(trends)


if __name__ == "__main__":
    main()