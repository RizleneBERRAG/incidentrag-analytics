import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.generate import Generator


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class UTF8JSONResponse(JSONResponse):
    """
    Réponse JSON forcée en UTF-8.
    """
    media_type = "application/json; charset=utf-8"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":")
        ).encode("utf-8")


app = FastAPI(
    title="IncidentRAG Analytics API",
    description=(
        "API RAG permettant de poser des questions sur un corpus CERT-FR "
        "et d'obtenir une réponse avec sources."
    ),
    version="1.0.0",
    default_response_class=UTF8JSONResponse
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AskRequest(BaseModel):
    """
    Requête envoyée à l'endpoint /ask.
    """
    question: str = Field(
        ...,
        min_length=3,
        description="Question utilisateur à poser au corpus CERT-FR."
    )


class Source(BaseModel):
    """
    Source utilisée pour construire la réponse.
    """
    id: str | None = None
    cert_id: str | None = None
    title: str | None = None
    date: str | None = None
    product: str | None = None
    url: str | None = None
    score: float | None = None
    excerpt: str | None = None


class AskResponse(BaseModel):
    """
    Réponse retournée par l'API.
    """
    question: str
    answer: str
    sources: List[Source]


@app.get("/", include_in_schema=False)
def interface() -> FileResponse:
    """
    Interface web de démonstration.
    """
    index_path = STATIC_DIR / "index.html"

    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Interface introuvable : app/static/index.html"
        )

    return FileResponse(index_path)


@app.get("/health")
def health() -> Dict[str, str]:
    """
    Vérifie que l'API est démarrée.
    """
    return {
        "status": "ok",
        "service": "incidentrag-api"
    }


@app.get("/api")
def api_info() -> Dict[str, Any]:
    """
    Informations techniques de l'API.
    """
    return {
        "project": "IncidentRAG Analytics",
        "status": "ok",
        "description": "API RAG sur un corpus CERT-FR.",
        "endpoints": {
            "interface": "GET /",
            "ask": "POST /ask",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> Dict[str, Any]:
    """
    Pose une question au système RAG.

    Pipeline :
    question -> retrieval Chroma -> génération de réponse -> sources.
    """
    try:
        generator = Generator()
        result = generator.answer(payload.question)

        return {
            "question": result.get("question", payload.question),
            "answer": result.get("answer", ""),
            "sources": result.get("sources", [])
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur pendant le traitement de la question : {error}"
        ) from error