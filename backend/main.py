from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from vanna.ollama import Ollama
from vanna.pgvector import PG_VectorStore

app = FastAPI()

# --- Configuration ---
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://admin:admin@db:5432/ai_cockpit')
MODEL_NAME = 'qwen2.5:14b'

# --- Vanna Setup ---
class MyVanna(PG_VectorStore, Ollama):
    def __init__(self, config=None):
        PG_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)

# Initialize Vanna
try:
    vn = MyVanna(config={
        'ollama_host': OLLAMA_HOST,
        'model': MODEL_NAME,
        'postgres_connection_string': POSTGRES_URL
    })
    print("✅ Vanna initialized successfully")
except Exception as e:
    print(f"❌ Error initializing Vanna: {e}")
    vn = None

# --- API Models ---
class Question(BaseModel):
    question: str

@app.get("/")
def read_root():
    return {"status": "AI Cockpit Backend is running", "model": MODEL_NAME}

@app.post("/api/chat")
def ask_ai(q: Question):
    if not vn:
        raise HTTPException(status_code=500, detail="Vanna AI is not initialized properly")

    try:
        # Check if GCP credentials exist, if so try to connect (Mock/Real)
        # For now, we just let Vanna generate SQL from Schema
        answer = vn.ask(question=q.question, print_results=False)

        # Convert result to JSON serializable format if needed
        return {
            "question": q.question,
            "answer": answer, # This might need parsing depending on Vanna version
            "sql": "SELECT * FROM placeholder" # Vanna usually returns SQL separately
        }
    except Exception as e:
        return {"error": str(e)}
