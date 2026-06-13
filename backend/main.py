"""
main.py

Vantage Backend API.

Exposes:
    GET  /                 -> health check
    POST /analyze          -> runs the full multi-agent pipeline and
                               returns graph data, scored grants,
                               policies, simulation results, and the
                               full agent reasoning log.

Run with:
    uvicorn main:app --reload --port 8000
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from orchestrator import VantageOrchestrator

app = FastAPI(title="Vantage API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok", "service": "vantage-api"}


@app.post("/analyze")
def analyze():
    """
    Runs the full Vantage multi-agent pipeline:
        Discovery -> Risk Scoring -> Policy Generation -> Simulation

    Returns the complete result for the frontend to render.
    """
    orchestrator = VantageOrchestrator()
    result = orchestrator.run()
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
