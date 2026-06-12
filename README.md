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
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── requirements.txt
│
├── scripts/
│   ├── fetch_corpus.sh
│   └── fetch_corpus.ps1
│
├── corpus/
│   ├── seed/
│   │   └── .gitkeep
│   └── raw/
│       └── .gitkeep
│
├── app/
│   ├── ingest.py
│   ├── embed.py
│   ├── store.py
│   ├── retrieve.py
│   ├── generate.py
│   ├── api.py
│   └── metrics.py
│
├── analytics/
│   ├── clustering.py
│   ├── trends.py
│   └── plots.py
│
├── docs/
│   └── COMPTE-RENDU.md

```



## Variables d'environnement

Copiez le fichier `.env.example` :

```bash
cp .env.example .env


```
## Licence des données

Les avis CERT-FR utilisés dans ce projet proviennent de données publiques mises à disposition par le CERT-FR.

Le corpus seed est utilisé à des fins pédagogiques.


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



##  Démonstration du système RAG

L’API FastAPI permet d’interroger le système RAG en temps réel.

---

###  1. Vérification de l’API

Le service est bien lancé et accessible :

![API running](docs/screenshots/Capturedecran20260612133614.png)

---

###  2. Requête utilisateur (POST /ask)

Une question est envoyée au système :

![Request](docs/screenshots/Capturedecran20260612133634.png)

---

###  3. Réponse générée par le système RAG

Le système retourne une réponse basée sur le corpus CERT-FR avec les sources associées :

![Response](docs/screenshots/Capturedecran20260612133650.png)

![Response](docs/screenshots/Capturedecran20260612133713.png)

![Response](docs/screenshots/Capturedecran20260612133730.png)

---

 Cela démontre le bon fonctionnement complet du pipeline :
ingestion → embeddings → retrieval → génération → API