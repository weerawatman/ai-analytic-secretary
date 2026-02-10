from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import pandas as pd
from vanna.ollama import Ollama
from vanna.pgvector import PG_VectorStore
from google.cloud import bigquery

# --- Configuration ---
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://admin:admin@db:5432/ai_cockpit')
MODEL_NAME = 'qwen2.5:14b'

# --- Custom Vanna Class ---
class MyVanna(Ollama, PG_VectorStore):
    def __init__(self, config=None):
        # Initialize parent classes
        Ollama.__init__(self, config=config)
        PG_VectorStore.__init__(self, config=config)

        # Initialize BigQuery Client
        try:
            print("DEBUG: Connecting to BigQuery...")
            self.bq_client = bigquery.Client.from_service_account_json('service_account.json')
            print("DEBUG: BigQuery Connected Successfully.")
        except Exception as e:
            print(f"ERROR: Failed to connect to BigQuery: {e}")

    def run_sql(self, sql: str) -> pd.DataFrame:
        print(f"DEBUG: Executing SQL: {sql}")
        try:
            job = self.bq_client.query(sql)
            df = job.to_dataframe()
            print(f"DEBUG: SQL Executed. Rows returned: {len(df)}")
            return df
        except Exception as e:
            print(f"ERROR: SQL Execution failed: {e}")
            return None

# --- Setup Vanna ---
config = {
    'ollama_host': OLLAMA_HOST,
    'model': MODEL_NAME,
    'connection_string': POSTGRES_URL
}
vn = MyVanna(config=config)

# --- API ---
app = FastAPI()

class ChatRequest(BaseModel):
    question: str

class TrainRequest(BaseModel):
    ddl: str | None = None
    documentation: str | None = None
    sql: str | None = None

@app.post("/api/chat")
def chat(request: ChatRequest):
    # 1. Generate SQL
    sql = vn.generate_sql(request.question)

    # 2. Execute SQL (Force use of our custom method)
    df = vn.run_sql(sql)

    # 3. Format Result
    data = []
    if df is not None and not df.empty:
        # Convert Timestamp/Date objects to string for JSON serialization
        df = df.astype(str)
        data = df.to_dict(orient='records')

    return {
        "question": request.question,
        "sql": sql,
        "answer": data
    }

@app.post("/api/train")
def train(request: TrainRequest):
    try:
        if request.ddl:
            vn.train(ddl=request.ddl)
        if request.documentation:
            vn.train(documentation=request.documentation)
        if request.sql:
            vn.train(sql=request.sql)
        return {"status": "success", "message": "Training completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/training_data")
def get_training_data():
    df = vn.get_training_data()
    if df is None or df.empty:
        return {"status": "success", "data": []}
    data = df.to_dict(orient='records')
    return {"status": "success", "data": data}
