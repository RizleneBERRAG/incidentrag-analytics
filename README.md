# IncidentRAG Analytics

## Présentation

IncidentRAG Analytics est un projet de TP basé sur la création d'un pipeline RAG analytique.

L'objectif est de permettre à un utilisateur de poser des questions sur un corpus d'avis de sécurité CERT-FR, puis d'obtenir une réponse générée à partir des passages les plus pertinents, avec les sources utilisées.

Le projet ne se limite pas à une simple question/réponse. Il doit aussi proposer une première analyse du corpus afin de faire ressortir des tendances : produits ou éditeurs les plus fréquents, catégories de risques, thèmes principaux ou évolution dans le temps.

## Projet choisi

Projet B - IncidentRAG Analytics
Vector store : Chroma
Corpus : avis de sécurité CERT-FR

## Équipe

* Rizlene Berrag
* Franck Joel Nzokou

## Répartition des rôles

* Rizlene Berrag : R1 Data / Ingestion + R4 DevOps / Analytics
* Franck Joel Nzokou : R2 Embeddings / Index + R3 Retrieval / LLM

## Objectifs principaux

* Récupérer un corpus d'avis de sécurité CERT-FR
* Extraire le contenu utile des documents
* Découper les textes en chunks
* Ajouter des métadonnées exploitables : titre, date, produit, catégorie, sévérité
* Générer des embeddings avec un modèle local
* Stocker les vecteurs dans Chroma
* Rechercher les passages les plus pertinents selon une question utilisateur
* Générer une réponse avec sources
* Exposer une API avec un endpoint `POST /ask`
* Produire une première analyse du corpus avec des graphiques ou tableaux

## Technologies prévues

* Python
* FastAPI
* Chroma
* Sentence Transformers
* Scikit-learn
* Matplotlib
* Docker / Docker Compose
* GitHub
* LLM gratuit selon disponibilité

## Structure du projet

```txt
incidentrag-analytics/
├── app/
│   ├── ingest.py       # Préparation et découpage du corpus
│   ├── embed.py        # Génération des embeddings
│   ├── store.py        # Connexion au vector store Chroma
│   ├── retrieve.py     # Recherche des passages pertinents
│   ├── generate.py     # Génération de réponse avec l'IA
│   ├── api.py          # API FastAPI
│   └── metrics.py      # Mesures de latence, tokens et qualité
│
├── analytics/
│   └── clustering.py   # Analyse du corpus et clustering
│
├── corpus/
│   └── .gitkeep        # Dossier du corpus local
│
├── docs/
│   └── COMPTE-RENDU.md # Compte rendu du projet
│
├── scripts/
│   └── fetch_corpus.ps1 # Récupération du corpus
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Lancement prévu

Installation des dépendances :

```bash
pip install -r requirements.txt
```

Lancement avec Docker Compose :

```bash
docker compose up --build
```

Endpoint prévu :

```http
POST /ask
```

Exemple de question :

```json
{
  "question": "Quels produits reviennent le plus souvent dans les avis de sécurité ?"
}
```

## État du projet

Projet en cours de démarrage.

Premières étapes réalisées ou prévues :

* Initialisation du dépôt GitHub
* Création de la structure du projet
* Préparation du README
* Préparation du compte rendu
* Répartition des rôles entre les membres
