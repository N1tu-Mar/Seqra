from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from scoring import score_sequence
from llm import parse_query, generate_candidate_summary, generate_session_summary
from generator import generate_sequences

app = FastAPI(title="Seqra API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class GenerateRequest(BaseModel):
    target_pathogen: Optional[str] = "unknown"
    gram_type: Optional[str] = "positive"
    min_length: Optional[int] = 15
    max_length: Optional[int] = 35
    max_toxicity: Optional[str] = "low"
    max_hemolysis: Optional[str] = "low"
    delivery_mode: Optional[str] = "topical"
    charge_preference: Optional[str] = "high"
    locked_residues: Optional[list] = []


class ScoreRequest(BaseModel):
    sequence: str


class SummarizeRequest(BaseModel):
    candidate: dict


@app.post("/parse_query")
def api_parse_query(req: QueryRequest):
    return parse_query(req.query)


@app.post("/generate")
def api_generate(req: GenerateRequest):
    params = req.model_dump()
    sequences = generate_sequences(params, n=8)
    scored = [score_sequence(s) for s in sequences]
    for c in scored:
        c["summary"] = generate_candidate_summary(c)
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    top5 = scored[:5]
    session_summary = generate_session_summary(top5)
    return {"candidates": top5, "session_summary": session_summary}


@app.post("/score")
def api_score(req: ScoreRequest):
    result = score_sequence(req.sequence)
    result["summary"] = generate_candidate_summary(result)
    return result


@app.get("/health")
def health():
    return {"status": "ok"}
