from pathlib import Path
import csv
import json
from collections import Counter, defaultdict


CHUNKS_FILE = Path("corpus/chunks.jsonl")
RESULTS_DIR = Path("analytics/results")
FIGURES_DIR = Path("docs/figures")


FRENCH_MONTHS = {
    "janvier": "01",
    "février": "02",
    "fevrier": "02",
    "mars": "03",
    "avril": "04",
    "mai": "05",
    "juin": "06",
    "juillet": "07",
    "août": "08",
    "aout": "08",
    "septembre": "09",
    "octobre": "10",
    "novembre": "11",
    "décembre": "12",
    "decembre": "12",
}


def load_chunks(path: Path) -> list[dict]:
    """
    Charge les chunks générés par app/ingest.py.
    """
    if not path.exists():
        print(f"Fichier introuvable : {path}")
        print("Lance d'abord : python app\\ingest.py")
        return []

    chunks = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    return chunks


def get_documents_from_chunks(chunks: list[dict]) -> dict:
    """
    Reconstitue une liste de documents uniques à partir des métadonnées des chunks.
    Un document CERT-FR possède plusieurs chunks, mais on ne veut compter le document qu'une seule fois.
    """
    documents = {}

    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        cert_id = metadata.get("cert_id", "")

        if cert_id and cert_id not in documents:
            documents[cert_id] = metadata

    return documents


def normalize_month(date_value: str) -> str:
    """
    Transforme une date française du type '10 juin 2026' en '2026-06'.
    """
    if not date_value:
        return "date inconnue"

    parts = date_value.lower().split()

    if len(parts) >= 3:
        month = FRENCH_MONTHS.get(parts[1], "")
        year = parts[2]

        if month and year.isdigit():
            return f"{year}-{month}"

    return "date inconnue"


def save_counter_to_csv(counter: Counter, output_file: Path, first_column: str, second_column: str) -> None:
    """
    Sauvegarde un compteur dans un fichier CSV.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([first_column, second_column])

        for key, value in counter.most_common():
            writer.writerow([key, value])


def generate_bar_chart(counter: Counter, title: str, xlabel: str, ylabel: str, output_file: Path, limit: int = 10) -> bool:
    """
    Génère un graphique simple avec matplotlib si la bibliothèque est disponible.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib n'est pas installé. Graphique non généré.")
        print("Pour l'installer : pip install matplotlib")
        return False

    if not counter:
        return False

    items = counter.most_common(limit)
    labels = [item[0] for item in items]
    values = [item[1] for item in items]

    output_file.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 6))
    plt.bar(labels, values)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

    return True


def analyze_corpus(chunks: list[dict]) -> dict:
    """
    Produit une première analyse simple du corpus.
    """
    documents = get_documents_from_chunks(chunks)

    product_counter = Counter()
    year_counter = Counter()
    month_counter = Counter()
    source_counter = Counter()
    chunks_by_document = Counter()

    for cert_id, metadata in documents.items():
        product = metadata.get("product") or "produit inconnu"
        year = metadata.get("year") or "année inconnue"
        date = metadata.get("date") or ""

        product_counter[product] += 1
        year_counter[year] += 1
        month_counter[normalize_month(date)] += 1
        source_counter[metadata.get("url", cert_id)] += 1

    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        cert_id = metadata.get("cert_id", "document inconnu")
        chunks_by_document[cert_id] += 1

    summary = {
        "total_chunks": len(chunks),
        "total_documents": len(documents),
        "top_products": product_counter.most_common(10),
        "documents_by_year": year_counter.most_common(),
        "documents_by_month": sorted(month_counter.items()),
        "chunks_by_document": chunks_by_document.most_common(10),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with (RESULTS_DIR / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    save_counter_to_csv(product_counter, RESULTS_DIR / "top_products.csv", "product", "documents_count")
    save_counter_to_csv(year_counter, RESULTS_DIR / "documents_by_year.csv", "year", "documents_count")
    save_counter_to_csv(month_counter, RESULTS_DIR / "documents_by_month.csv", "month", "documents_count")
    save_counter_to_csv(chunks_by_document, RESULTS_DIR / "chunks_by_document.csv", "cert_id", "chunks_count")

    generate_bar_chart(
        product_counter,
        "Top produits affectés dans les avis CERT-FR",
        "Produit",
        "Nombre d'avis",
        FIGURES_DIR / "top_products.png"
    )

    generate_bar_chart(
        chunks_by_document,
        "Nombre de chunks par avis CERT-FR",
        "Avis CERT-FR",
        "Nombre de chunks",
        FIGURES_DIR / "chunks_by_document.png"
    )

    return summary


def print_summary(summary: dict) -> None:
    """
    Affiche les résultats principaux dans le terminal.
    """
    print()
    print("Analyse du corpus CERT-FR")
    print("-------------------------")
    print(f"Nombre de documents : {summary['total_documents']}")
    print(f"Nombre de chunks : {summary['total_chunks']}")

    print()
    print("Top produits affectés :")
    for product, count in summary["top_products"]:
        print(f"- {product} : {count} avis")

    print()
    print("Documents par mois :")
    for month, count in summary["documents_by_month"]:
        print(f"- {month} : {count} avis")

    print()
    print("Chunks par document :")
    for cert_id, count in summary["chunks_by_document"]:
        print(f"- {cert_id} : {count} chunks")

    print()
    print(f"Résultats générés dans : {RESULTS_DIR}")
    print(f"Graphiques générés dans : {FIGURES_DIR}")


def main():
    chunks = load_chunks(CHUNKS_FILE)

    if not chunks:
        print("Aucun chunk à analyser.")
        return

    summary = analyze_corpus(chunks)
    print_summary(summary)


if __name__ == "__main__":
    main()