# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import llm

# Define an async context manager for application lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        llm.load_model_and_tokenizer()
        print("LLM model loaded successfully.")
    except Exception as e:
        raise RuntimeError(f"Failed to load LLM model at startup: {e}")
    yield
    print("Shutting down application: No specific cleanup needed for LLM.")

app = FastAPI(lifespan=lifespan)

class Implementation(BaseModel): # expected structure of the JSON payload that the backend will send to /get_embedding/
    code: str

@app.post("/get_embedding/")
async def get_embedding(implementation: Implementation):
    if llm.model is None or llm.tokenizer is None:
        raise HTTPException(status_code=503, detail="LLM model is not loaded or ready.")

    try:
        code_embedding = llm.calculate_code_embedding(implementation.code)
        return {"embedding": code_embedding}
    except Exception as e:
        print(f"Error during embedding calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate embedding: {e}")


@app.get("/health/")
async def health_check():
    model_loaded = llm.model is not None and llm.tokenizer is not None
    return {"status": "healthy", "model_loaded": model_loaded}