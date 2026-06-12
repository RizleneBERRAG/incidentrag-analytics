# Compte rendu — IncidentRAG Analytics

## 1. Introduction

Le projet **IncidentRAG Analytics** consiste à construire un pipeline RAG autour d'un corpus d'avis de sécurité CERT-FR.

L'objectif est de permettre à un utilisateur de poser une question en langage naturel sur des avis de sécurité, puis d'obtenir une réponse basée sur les passages les plus pertinents retrouvés dans le corpus.

Le projet doit également fournir une analyse du corpus afin de dégager des tendances : produits récurrents, volume de documents, répartition temporelle et statistiques sur les chunks générés.

---

## 2. Projet choisi

Nous avons choisi le **Projet B — IncidentRAG Analytics**.

Les choix techniques principaux sont les suivants :

* **Corpus** : avis de sécurité CERT-FR
* **Vector store** : Chroma
* **API** : FastAPI
* **Modèle d'embedding** : `sentence-transformers/all-MiniLM-L6-v2`
* **Interface** : page web intégrée à l'API
* **Déploiement** : Docker Compose

---

## 3. Équipe et répartition des rôles

Le projet a été réalisé par :

* Rizlene Berrag
* Franck Joel Nzokou

La répartition initiale était la suivante :

| Membre             | Rôle                  | Responsabilités                                                                                                    |
| ------------------ | --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Rizlene Berrag     | R1 Data / Ingestion   | Récupération du corpus, extraction du texte utile, nettoyage HTML, extraction des métadonnées, découpage en chunks |
| Rizlene Berrag     | R4 DevOps / Analytics | Analyse du corpus, génération des résultats CSV/JSON, graphiques, Docker, interface web, finalisation du rendu     |
| Franck Joel Nzokou | R2 Embeddings / Index | Génération des embeddings, indexation dans Chroma                                                                  |
| Franck Joel Nzokou | R3 Retrieval / LLM    | Recherche des chunks pertinents, génération de réponse, API RAG                                                    |

En fin de projet, certaines briques ont été reprises et finalisées afin d'obtenir un MVP complet, testable et présentable.

---

## 4. Objectifs du projet

Les objectifs principaux étaient :

* récupérer un corpus d'avis CERT-FR ;
* extraire les contenus utiles depuis des fichiers HTML ;
* nettoyer les données ;
* extraire des métadonnées exploitables ;
* découper les documents en chunks ;
* générer des embeddings ;
* indexer les chunks dans Chroma ;
* rechercher les passages les plus pertinents selon une question ;
* générer une réponse structurée avec sources ;
* exposer un endpoint `POST /ask` ;
* proposer une interface web de démonstration ;
* produire une première analyse du corpus.

---

## 5. Architecture globale

L'architecture du projet suit le principe suivant :

```txt
Avis CERT-FR
    ↓
Récupération du corpus
    ↓
Nettoyage et ingestion
    ↓
Découpage en chunks
    ↓
Génération d'embeddings
    ↓
Indexation dans Chroma
    ↓
Recherche vectorielle
    ↓
Réponse avec sources
    ↓
API FastAPI + interface web
```

Cette architecture permet de séparer clairement les responsabilités :

* `scripts/fetch_corpus.ps1` récupère les avis CERT-FR ;
* `app/ingest.py` nettoie et découpe les documents ;
* `app/embed.py` génère les embeddings ;
* `app/store.py` gère Chroma ;
* `app/retrieve.py` recherche les passages pertinents ;
* `app/generate.py` construit une réponse à partir des passages retrouvés ;
* `app/api.py` expose l'API et l'interface web ;
* `analytics/clustering.py` produit les statistiques du corpus.

---

## 6. Ingestion du corpus

La première étape a consisté à récupérer des avis de sécurité CERT-FR.

Le script PowerShell `scripts/fetch_corpus.ps1` permet de télécharger automatiquement des avis depuis le site CERT-FR et de les stocker dans le dossier :

```txt
corpus/raw/
```

Les fichiers HTML récupérés sont ensuite traités par :

```txt
app/ingest.py
```

Ce script effectue plusieurs opérations :

* lecture des fichiers HTML ;
* extraction du texte utile ;
* suppression du bruit lié à la navigation ;
* correction de l'encodage ;
* extraction des métadonnées ;
* découpage en chunks ;
* génération du fichier final `corpus/chunks.jsonl`.

Les métadonnées extraites sont notamment :

* identifiant CERT-FR ;
* titre de l'avis ;
* date ;
* produit concerné ;
* systèmes affectés ;
* risques ;
* source ;
* URL.

---

## 7. Découpage en chunks

Le corpus est découpé en chunks afin d'être exploitable par un système RAG.

Le fichier généré est :

```txt
corpus/chunks.jsonl
```

Chaque ligne correspond à un chunk contenant :

* un identifiant unique ;
* le texte du chunk ;
* les métadonnées associées.

Sur le corpus testé, le pipeline a généré :

```txt
10 documents analysés
226 chunks générés
```

Ce fichier constitue la base utilisée pour l'indexation vectorielle.

---

## 8. Embeddings et indexation Chroma

Le fichier :

```txt
app/embed.py
```

charge les chunks depuis `corpus/chunks.jsonl`, puis utilise le modèle :

```txt
sentence-transformers/all-MiniLM-L6-v2
```

pour générer les embeddings.

Les vecteurs sont ensuite stockés dans Chroma via :

```txt
app/store.py
```

La collection utilisée est :

```txt
rag_chunks
```

Chroma est lancé avec Docker Compose. En local, il est exposé sur :

```txt
localhost:8001
```

Dans Docker, l'API communique avec le service Chroma via :

```txt
CHROMA_HOST=chroma
CHROMA_PORT=8000
```

L'indexation a été testée avec succès sur les 226 chunks du corpus.

---

## 9. Recherche vectorielle

Le fichier :

```txt
app/retrieve.py
```

permet d'encoder une question utilisateur avec le même modèle d'embedding, puis de rechercher dans Chroma les chunks les plus proches.

Exemple de question testée :

```txt
Quelles vulnérabilités concernent Microsoft Windows ?
```

Le système a correctement retrouvé comme premier résultat :

```txt
CERTFR-2026-AVI-0728 — Multiples vulnérabilités dans Microsoft Windows
```

Ce résultat valide le fonctionnement de la recherche sémantique.

---

## 10. Génération de réponse avec sources

Le fichier :

```txt
app/generate.py
```

construit une réponse à partir des passages retrouvés.

Le système retourne :

* la question posée ;
* une réponse structurée ;
* les sources utilisées ;
* les métadonnées des sources ;
* un extrait de chaque chunk.

La réponse est volontairement basée uniquement sur le corpus indexé afin d'éviter les hallucinations.

Le système fonctionne sans dépendance obligatoire à une API LLM externe. Cela permet une démonstration stable et reproductible, même sans clé API.

---

## 11. API FastAPI

L'API est définie dans :

```txt
app/api.py
```

Elle expose notamment :

```txt
GET /
GET /health
GET /api
POST /ask
GET /docs
```

Le endpoint principal est :

```txt
POST /ask
```

Exemple de requête :

```json
{
  "question": "Quelles vulnérabilités concernent Microsoft Windows ?"
}
```

Exemple de réponse :

```json
{
  "question": "Quelles vulnérabilités concernent Microsoft Windows ?",
  "answer": "D'après les avis CERT-FR retrouvés dans le corpus...",
  "sources": [
    {
      "cert_id": "CERTFR-2026-AVI-0728",
      "title": "Multiples vulnérabilités dans Microsoft Windows",
      "url": "https://www.cert.ssi.gouv.fr/avis/CERTFR-2026-AVI-0728/"
    }
  ]
}
```

---

## 12. Interface web

Une interface web a été ajoutée dans :

```txt
app/static/index.html
```

Elle permet de tester le système sans passer par Swagger ou PowerShell.

L'interface propose :

* une zone de question ;
* un bouton d'envoi ;
* des exemples de questions ;
* l'affichage de la réponse ;
* l'affichage des sources ;
* un résumé technique du système.

Cette interface facilite la démonstration du projet.

---

## 13. Analyse du corpus

Le script :

```txt
analytics/clustering.py
```

réalise une analyse simple du corpus.

Il génère plusieurs fichiers :

```txt
analytics/results/summary.json
analytics/results/top_products.csv
analytics/results/documents_by_month.csv
analytics/results/documents_by_year.csv
analytics/results/chunks_by_document.csv
```

Il génère également des graphiques :

```txt
docs/figures/top_products.png
docs/figures/chunks_by_document.png
```

Les résultats obtenus sur le corpus testé sont :

```txt
Nombre de documents : 10
Nombre de chunks : 226
Période : juin 2026
```

Produits détectés dans le corpus :

* Typo3
* Stormshield Network Security
* Ivanti
* Fortinet
* Microsoft Edge
* Microsoft Office
* Microsoft Windows
* Microsoft .Net
* Microsoft Azure
* produits Microsoft

Cette analyse permet d'avoir une vision globale du corpus avant même d'interroger le système RAG.

---

## 14. Docker et déploiement

Le projet contient :

```txt
Dockerfile
docker-compose.yml
.dockerignore
```

Le `docker-compose.yml` lance deux services :

* `chroma` : base vectorielle ChromaDB ;
* `api` : API FastAPI du projet.

Commandes principales :

```bash
docker compose up --build
```

Si la base Chroma est vide :

```bash
docker compose run --rm api python -m app.embed
```

L'interface est ensuite accessible sur :

```txt
http://127.0.0.1:8000
```

---

## 15. Tests effectués

Plusieurs tests ont été réalisés.

### Test d'ingestion

```bash
python -m app.ingest
```

Résultat :

```txt
10 documents HTML trouvés
226 chunks générés
```

### Test d'analyse

```bash
python -m analytics.clustering
```

Résultat :

```txt
summary.json généré
CSV générés
graphiques générés
```

### Test d'indexation

```bash
python -m app.embed
```

Résultat :

```txt
226 chunks indexés dans Chroma
```

### Test de retrieval

```bash
python -m app.retrieve
```

Résultat :

```txt
CERTFR-2026-AVI-0728 — Multiples vulnérabilités dans Microsoft Windows
```

### Test de génération

```bash
python -m app.generate
```

Résultat :

```txt
Réponse structurée avec sources CERT-FR
```

### Test API

```powershell
$body = @{
    question = "Quelles vulnérabilités concernent Microsoft Windows ?"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/ask" `
  -Method POST `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

Résultat :

```txt
question
answer
sources
```

---

## 16. Difficultés rencontrées

Plusieurs difficultés ont été rencontrées pendant le projet.

### Nettoyage HTML

Les pages CERT-FR contiennent du bruit : navigation, menus, mentions répétées, contenus techniques longs. Il a fallu extraire seulement les parties utiles.

### Encodage

Certains contenus affichaient des caractères incorrects. Un travail a été nécessaire pour nettoyer les textes et limiter les problèmes d'encodage.

### Métadonnées

Les informations utiles ne sont pas toujours structurées de la même manière. Il a donc fallu prévoir une extraction tolérante.

### Chroma

L'utilisation de Chroma demande de bien distinguer :

* le port local exposé sur la machine ;
* le port utilisé entre conteneurs Docker ;
* le nom du service Docker.

### PowerShell

Lors des tests API, PowerShell affichait parfois mal les accents, même lorsque l'API retournait bien du JSON UTF-8. Cela a été identifié comme un problème d'affichage terminal et non comme un problème du backend.

---

## 17. Limites du projet

Le projet constitue un MVP fonctionnel.

La limite principale est que la génération de réponse ne repose pas encore sur un grand modèle de langage externe connecté. Le système construit une réponse à partir des passages retrouvés dans le corpus.

Ce choix permet :

* de limiter les coûts ;
* de garantir une démonstration reproductible ;
* d'éviter les hallucinations ;
* de garder une réponse basée sur les sources.

Cependant, les réponses peuvent être moins naturelles ou moins synthétiques qu'avec un LLM complet.

Améliorations possibles :

* brancher un LLM local ou externe ;
* améliorer la reformulation des réponses ;
* enrichir les métadonnées ;
* ajouter un historique des conversations ;
* ajouter des tests automatisés ;
* améliorer l'analyse des risques ;
* proposer un tableau de bord analytics intégré.

---

## 18. Conclusion

Le projet a permis de construire un pipeline RAG complet autour d'un corpus CERT-FR.

Le système permet aujourd'hui de :

* récupérer et préparer un corpus ;
* découper les avis en chunks ;
* générer des embeddings ;
* indexer les chunks dans Chroma ;
* rechercher les passages les plus pertinents ;
* produire une réponse avec sources ;
* interroger le système via une API ;
* utiliser une interface web de démonstration ;
* analyser le corpus avec des fichiers CSV/JSON et des graphiques.

Le pipeline final est donc fonctionnel, testable et démontrable.
