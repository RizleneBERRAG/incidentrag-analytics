from fastapi import FastAPI
from pydantic import BaseModel

from app.generate import Generator


app = FastAPI(title="IncidentRAG API")

generator = Generator()


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "message": "IncidentRAG API is running"
    }


@app.post("/ask")
def ask(req: QuestionRequest):
    """
    Endpoint principal RAG.
    """

    result = generator.answer(req.question)

    return {
        "question": result["question"],
        "answer": result["answer"],
        "sources": result["sources"]
    }