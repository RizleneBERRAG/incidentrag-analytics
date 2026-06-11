from pathlib import Path
from html.parser import HTMLParser
import html as html_lib
import json
import re


CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

RAW_CORPUS_DIR = Path("corpus/raw")
OUTPUT_FILE = Path("corpus/chunks.jsonl")


class HTMLTextExtractor(HTMLParser):
    """
    Extrait le texte brut d'un fichier HTML.
    """

    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.skip = True

        if tag in {"p", "div", "section", "article", "h1", "h2", "h3", "li", "br", "tr", "td"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.skip = False

        if tag in {"p", "div", "section", "article", "h1", "h2", "h3", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text:
                self.parts.append(text)

    def get_text(self):
        return " ".join(self.parts)


def clean_text(text: str) -> str:
    """
    Nettoie le texte extrait du HTML.
    """
    text = html_lib.unescape(text)
    text = text.replace("\ufeff", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def html_to_text(html_content: str) -> str:
    """
    Transforme une page HTML en texte brut.
    """
    parser = HTMLTextExtractor()
    parser.feed(html_content)
    return clean_text(parser.get_text())


def keep_certfr_useful_content(text: str) -> str:
    """
    Supprime une partie du bruit de navigation du site CERT-FR.
    On garde principalement le contenu de l'avis.
    """
    start_markers = [
        "Paris, le ",
        "Affaire suivie par:",
        "Avis du CERT-FR",
        "Gestion du document",
        "Référence CERTFR",
    ]

    start_positions = []

    for marker in start_markers:
        position = text.find(marker)
        if position != -1:
            start_positions.append(position)

    if start_positions:
        text = text[min(start_positions):]

    end_markers = [
        "Retour en haut de page",
        "Plan du site",
        "Flux RSS complet",
    ]

    for marker in end_markers:
        position = text.find(marker)
        if position != -1:
            text = text[:position]

    return clean_text(text)


def extract_title(html_content: str, fallback: str) -> str:
    """
    Extrait un titre depuis la balise h1 ou title.
    """
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_content, re.IGNORECASE | re.DOTALL)

    if h1_match:
        title = html_to_text(h1_match.group(1))
        return title.replace("Objet:", "").strip()

    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)

    if title_match:
        title = html_to_text(title_match.group(1))
        title = title.replace("- CERT-FR", "").strip()
        return title.replace("Objet:", "").strip()

    return fallback


def extract_cert_id(file_path: Path) -> str:
    """
    Extrait l'identifiant CERT-FR depuis le nom du fichier.
    Exemple : CERTFR-2026-AVI-0731
    """
    match = re.search(r"CERTFR-\d{4}-AVI-\d{4}", file_path.name)

    if match:
        return match.group(0)

    return file_path.stem


def extract_year(cert_id: str) -> str:
    """
    Extrait l'année depuis l'identifiant CERT-FR.
    """
    match = re.search(r"CERTFR-(\d{4})-AVI-\d{4}", cert_id)

    if match:
        return match.group(1)

    return ""


def extract_first_version_date(text: str) -> str:
    """
    Extrait la date de première version si elle est présente.
    """
    match = re.search(r"Date de la première version\s+([0-9]{1,2}\s+\w+\s+\d{4})", text)

    if match:
        return match.group(1)

    match = re.search(r"Paris, le\s+([0-9]{1,2}\s+\w+\s+\d{4})", text)

    if match:
        return match.group(1)

    return ""


def extract_risks(text: str) -> str:
    """
    Extrait la partie Risque(s) si elle est présente.
    """
    match = re.search(r"Risque\(s\)\s+(.*?)\s+Syst", text)

    if match:
        return clean_text(match.group(1))

    return ""


def extract_systems(text: str) -> str:
    """
    Extrait la partie systèmes affectés si elle est présente.
    """
    patterns = [
        r"Système\(s\) affecté\(s\)\s+(.*?)\s+Résumé",
        r"Systèmes affectés\s+(.*?)\s+Résumé",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return clean_text(match.group(1))

    return ""


def extract_product_from_title(title: str) -> str:
    """
    Essaie d'extraire le produit depuis le titre.
    Exemple : Multiples vulnérabilités dans Typo3 -> Typo3
    """
    match = re.search(r"dans\s+(.+)$", title, re.IGNORECASE)

    if match:
        return match.group(1).strip()

    return ""


def read_html_documents(corpus_dir: Path) -> list[dict]:
    """
    Lit les fichiers HTML téléchargés dans corpus/raw.
    """
    documents = []

    if not corpus_dir.exists():
        print(f"Le dossier {corpus_dir} n'existe pas encore.")
        return documents

    html_files = sorted(corpus_dir.glob("*.html"))

    for file_path in html_files:
        html_content = file_path.read_text(encoding="utf-8", errors="ignore")

        cert_id = extract_cert_id(file_path)
        title = extract_title(html_content, cert_id)

        full_text = html_to_text(html_content)
        useful_text = keep_certfr_useful_content(full_text)

        if not useful_text:
            continue

        documents.append({
            "cert_id": cert_id,
            "title": title,
            "year": extract_year(cert_id),
            "date": extract_first_version_date(useful_text),
            "product": extract_product_from_title(title),
            "risks": extract_risks(useful_text),
            "systems": extract_systems(useful_text),
            "source": str(file_path),
            "url": f"https://www.cert.ssi.gouv.fr/avis/{cert_id}/",
            "content": useful_text
        })

    return documents


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Découpe un texte en morceaux de taille fixe avec chevauchement.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def build_chunks(documents: list[dict]) -> list[dict]:
    """
    Transforme les documents en chunks avec métadonnées.
    """
    all_chunks = []

    for doc in documents:
        chunks = chunk_text(doc["content"])

        for index, chunk in enumerate(chunks):
            chunk_id = f"{doc['cert_id']}_chunk_{index:03d}"

            all_chunks.append({
                "id": chunk_id,
                "text": chunk,
                "metadata": {
                    "cert_id": doc["cert_id"],
                    "title": doc["title"],
                    "year": doc["year"],
                    "date": doc["date"],
                    "product": doc["product"],
                    "risks": doc["risks"],
                    "systems": doc["systems"],
                    "source": doc["source"],
                    "url": doc["url"],
                    "chunk_index": index,
                    "document_type": "avis_certfr"
                }
            })

    return all_chunks


def save_chunks(chunks: list[dict], output_file: Path) -> None:
    """
    Sauvegarde les chunks au format JSONL.
    Un chunk = une ligne JSON.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def main():
    print("Démarrage de l'ingestion du corpus CERT-FR...")

    documents = read_html_documents(RAW_CORPUS_DIR)
    print(f"Documents HTML trouvés : {len(documents)}")

    chunks = build_chunks(documents)
    print(f"Chunks générés : {len(chunks)}")

    save_chunks(chunks, OUTPUT_FILE)
    print(f"Fichier généré : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()