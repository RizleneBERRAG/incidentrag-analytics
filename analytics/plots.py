from pathlib import Path
import json

import matplotlib.pyplot as plt


RESULTS_FILE = Path("analytics/results/summary.json")
OUTPUT_DIR = Path("docs/figures")


def load_summary():
    if not RESULTS_FILE.exists():
        print("Aucun fichier summary.json trouvé.")
        return None

    with RESULTS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def plot_top_products(summary):
    products = summary.get("top_products", [])

    if not products:
        return

    labels = [p[0] for p in products]
    values = [p[1] for p in products]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.title("Top produits affectés (CERT-FR)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_DIR / "top_products.png")
    plt.close()


def plot_documents_by_year(summary):
    data = summary.get("documents_by_year", [])

    if not data:
        return

    years = [d[0] for d in data]
    counts = [d[1] for d in data]

    plt.figure(figsize=(8, 4))
    plt.plot(years, counts, marker="o")
    plt.title("Évolution des avis CERT-FR par année")
    plt.xticks(rotation=45)
    plt.tight_layout()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_DIR / "documents_by_year.png")
    plt.close()


def main():
    summary = load_summary()

    if not summary:
        return

    plot_top_products(summary)
    plot_documents_by_year(summary)

    print("Graphiques générés dans docs/figures")


if __name__ == "__main__":
    main()