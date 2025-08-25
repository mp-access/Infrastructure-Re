# api.py
import logging

# Basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import llm

from typing import List

# define an async context manager for application lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        llm.load_model_and_tokenizer()
        logger.info("LLM model loaded successfully.")
    except Exception as e:
        raise RuntimeError(f"Failed to load LLM model at startup: {e}")
    yield
    logger.info("Shutting down application: No specific cleanup needed for LLM.")

app = FastAPI(lifespan=lifespan)

class BatchRequestItem(BaseModel):
    submissionId: int
    codeSnippet: str

class BatchResponseItem(BaseModel):
    submissionId: int
    embedding: List[float]

@app.post("/calculate_embeddings/", response_model=List[BatchResponseItem])
async def get_embeddings(submissions: List[BatchRequestItem]):
    if llm.onnx_session is None or llm.tokenizer is None:
        raise HTTPException(status_code=503, detail="LLM model is not loaded or ready.")

    submission_ids = [sub.submissionId for sub in submissions]
    code_snippets = [sub.codeSnippet for sub in submissions]

    try:
        embeddings = llm.calculate_code_embeddings(code_snippets)

        response_data = []
        for i, embedding in enumerate(embeddings):
            response_data.append({
                "submissionId": submission_ids[i],
                "embedding": embedding
            })

        return response_data

    except Exception as e:
        logger.error(f"Error during batch embedding calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate batch embeddings: {e}")

@app.get("/health/")
async def health_check():
    model_loaded = llm.onnx_session is not None and llm.tokenizer is not None
    return JSONResponse(
        content={"status": "running", "model_loaded": model_loaded},
        media_type="application/json"
    )