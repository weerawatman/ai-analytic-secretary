from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from vanna.ollama import Ollama
from vanna.pgvector import PG_VectorStore

app = FastAPI()

# --- Configuration ---
# อ่านค่า Environment Variable
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
# กำหนดค่า Default ให้ชัดเจน ถ้าอ่านจาก Env ไม่ได้
POSTGRES_URL = os.getenv('POSTGRES_URL')
if not POSTGRES_URL:
    POSTGRES_URL = 'postgresql://admin:admin@db:5432/ai_cockpit'

MODEL_NAME = 'qwen2.5:14b'

# --- Debug Print (เช็คค่าก่อนเริ่มระบบ) ---
print(f"DEBUG: --- Starting Vanna Initialization ---")
print(f"DEBUG: Ollama Host: {OLLAMA_HOST}")
print(f"DEBUG: Postgres URL: {POSTGRES_URL}")
print(f"DEBUG: Model Name: {MODEL_NAME}")

# --- Vanna Setup ---
class MyVanna(PG_VectorStore, Ollama):
    def __init__(self, config=None):
        if config is None:
            config = {}
        
        # Print ดูว่า Config ที่ส่งเข้ามาหน้าตาเป็นยังไง
        print(f"DEBUG: Init Config received: {config}")

        # Initialize ส่วนต่างๆ
        try:
            PG_VectorStore.__init__(self, config=config)
            print("DEBUG: PG_VectorStore initialized OK")
            Ollama.__init__(self, config=config)
            print("DEBUG: Ollama initialized OK")
        except Exception as e:
            print(f"DEBUG: Error inside MyVanna __init__: {e}")
            raise e

# Initialize Vanna (Global Instance)
# ส่งค่า config แบบ "หว่านแห" (ป้องกัน Vanna เปลี่ยนชื่อ key)
config_payload = {
    'ollama_host': OLLAMA_HOST,
    'model': MODEL_NAME,
    'connection_string': POSTGRES_URL,         # ชื่อมาตรฐาน
    'postgres_connection_string': POSTGRES_URL # ชื่อเผื่อเวอร์ชันเก่า
}

vn = MyVanna(config=config_payload)
print("✅ Vanna initialized successfully")

# --- API Models ---
class Question(BaseModel):
    question: str

@app.get("/")
def read_root():
    status = "Running" if vn else "Error: Vanna not initialized"
    return {"status": status, "model": MODEL_NAME}

@app.post("/api/chat")
def ask_ai(q: Question):
    if not vn:
        raise HTTPException(status_code=500, detail="Vanna AI is not initialized properly. Check backend logs.")
    
    try:
        # ถาม Vanna
        answer = vn.ask(question=q.question, print_results=False)
        return {
            "question": q.question,
            "answer": str(answer), 
            "sql": "SQL log inside container" 
        }
    except Exception as e:
        return {"error": str(e)}