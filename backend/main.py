from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import re
import json
import pandas as pd
import plotly
import plotly.express as px
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str

class TrainRequest(BaseModel):
    ddl: str | None = None
    documentation: str | None = None
    sql: str | None = None

# --- Intent Classification (Router) ---
GREETING_PATTERNS = [
    r'(สวัสดี|หวัดดี|ดีจ้า|ดีค่ะ|ดีครับ)',
    r'^(hello|hi|hey|yo)[\s!?.]*$',
    r'good\s*(morning|afternoon|evening|night)',
    r'(สบายดี|เป็นไง|ทำอะไรอยู่)',
    r'(ขอบคุณ|ขอบใจ|thank|thanks)',
    r'(bye|ลาก่อน|ไปก่อน|ไปล่ะ)',
    r'(who are you|คุณคือใคร|คุณเป็นใคร|ชื่ออะไร|เป็นใคร)',
    r'(help|ช่วยอะไรได้|ทำอะไรได้บ้าง)',
    r'^(ดี|hey|ok|โอเค|เฮ้|หวัดดี)[\s!?.]*$',
]

DATA_KEYWORDS = [
    'ยอดขาย', 'ยอด', 'ขาย', 'ลูกค้า', 'สินค้า', 'รายได้', 'กำไร', 'ต้นทุน',
    'revenue', 'sales', 'customer', 'product', 'profit', 'cost', 'price',
    'table', 'query', 'report', 'select', 'from', 'where',
    'สูงสุด', 'ต่ำสุด', 'เฉลี่ย', 'รวม', 'จำนวน', 'เท่าไหร่', 'กี่',
    'max', 'min', 'average', 'total', 'count', 'sum',
    'order', 'ออเดอร์', 'invoice', 'payment', 'stock', 'inventory',
    'แสดง', 'ดึงข้อมูล', 'หา', 'ค้นหา', 'รายการ', 'สรุป',
]


def classify_intent(question: str) -> str:
    """Classify user intent as 'chat' or 'data'."""
    q = question.strip().lower()

    # Check data keywords first (higher priority)
    for keyword in DATA_KEYWORDS:
        if keyword in q:
            return 'data'

    # Check greeting/general patterns
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, q, re.IGNORECASE):
            return 'chat'

    # Short inputs without data keywords -> chat
    if len(q) < 15:
        return 'chat'

    # Default to data for longer queries (likely a business question)
    return 'data'


def detect_persona(question: str) -> tuple:
    """Detect persona based on Thai politeness particles.
    Returns (name, particle) tuple.
    """
    q = question.strip()
    if q.endswith('ค่ะ') or q.endswith('คะ'):
        return ('พิม', 'ค่ะ', 'คะ', 'ดิฉัน')
    elif q.endswith('ครับ'):
        return ('โจ', 'ครับ', 'ครับ', 'ผม')
    else:
        return ('AI Assistant', 'ครับ', 'ครับ', 'ผม')


def generate_chat_response(question: str) -> str:
    """Generate a friendly Thai chat response based on persona."""
    q = question.strip().lower()
    name, end_p, question_p, pronoun = detect_persona(question)

    # Greeting
    if re.search(r'(สวัสดี|hello|hi|hey|หวัดดี|ดีจ้า|ดีค่ะ|ดีครับ|^ดี)', q, re.IGNORECASE):
        return f'สวัสดี{end_p} {pronoun}ชื่อ{name} เป็นผู้ช่วยวิเคราะห์ข้อมูลธุรกิจ{end_p} มีเรื่องข้อมูลอะไรให้ช่วยไหม{question_p}?'

    # How are you
    if re.search(r'(สบายดี|เป็นไง)', q):
        return f'สบายดี{end_p} ขอบคุณที่ถามนะ{question_p} มีอะไรให้ช่วยวิเคราะห์ข้อมูลไหม{question_p}?'

    # Thank you
    if re.search(r'(ขอบคุณ|ขอบใจ|thank)', q, re.IGNORECASE):
        return f'ยินดี{end_p} หากมีอะไรให้ช่วยเพิ่มเติม บอกได้เลยนะ{question_p}'

    # Who are you
    if re.search(r'(who are you|คุณคือใคร|คุณเป็นใคร|ชื่ออะไร|เป็นใคร)', q, re.IGNORECASE):
        return f'{pronoun}ชื่อ{name}{end_p} เป็น AI ผู้ช่วยวิเคราะห์ข้อมูลธุรกิจ{end_p} สามารถถามเกี่ยวกับยอดขาย ลูกค้า สินค้า และข้อมูลอื่น ๆ ได้เลย{question_p}'

    # Help / What can you do
    if re.search(r'(help|ช่วย|ทำอะไรได้)', q, re.IGNORECASE):
        return f'{pronoun}สามารถช่วยวิเคราะห์ข้อมูลธุรกิจได้{end_p} เช่น ถามเรื่องยอดขาย ลูกค้า สินค้าขายดี หรือสรุปข้อมูลต่าง ๆ ลองถามได้เลยนะ{question_p}'

    # Bye
    if re.search(r'(bye|ลาก่อน|ไปก่อน|ไปล่ะ)', q, re.IGNORECASE):
        return f'ลาก่อนนะ{question_p} แล้วพบกันใหม่{end_p}'

    # Default fallback
    return f'{pronoun}ชื่อ{name}{end_p} เป็นผู้ช่วยวิเคราะห์ข้อมูลธุรกิจ{end_p} ลองถามเกี่ยวกับข้อมูลธุรกิจได้เลยนะ{question_p}'


@app.post("/api/chat")
def chat(request: ChatRequest):
    question = request.question.strip()
    intent = classify_intent(question)
    print(f"DEBUG: Question='{question}' | Intent='{intent}'")

    # --- Chat / Greeting ---
    if intent == 'chat':
        message = generate_chat_response(question)
        return {
            "type": "chat",
            "message": message,
            "sql": None,
            "data": None,
        }

    # --- Data Query ---
    try:
        sql = vn.generate_sql(question)
        print(f"DEBUG: Generated SQL: {sql}")

        # 1. Execute SQL
        df = vn.run_sql(sql)

        data = []
        if df is not None and not df.empty:
            data = df.astype(str).to_dict(orient='records')

        # 2. Generate Plotly Chart
        chart_json = None
        try:
            if df is not None and not df.empty:
                code = vn.generate_plotly_code(question=question, sql=sql, df=df)
                fig = vn.get_plotly_figure(plotly_code=code, df=df)
                if fig is not None:
                    chart_json = fig.to_json()
                    print("DEBUG: Plotly chart generated successfully.")
        except Exception as chart_err:
            print(f"WARNING: Chart generation failed (non-fatal): {chart_err}")
            chart_json = None

        # 3. Generate Storytelling / AI Insight
        analysis = None
        try:
            if df is not None and not df.empty:
                df_summary = df.head(20).to_string(index=False)
                insight_prompt = (
                    f"คุณเป็นนักวิเคราะห์ข้อมูลธุรกิจ ผู้ใช้ถามว่า: \"{question}\"\n"
                    f"SQL ที่ใช้: {sql}\n"
                    f"ผลลัพธ์ข้อมูล:\n{df_summary}\n\n"
                    f"กรุณาวิเคราะห์ข้อมูลนี้เป็นภาษาไทย สรุปสั้น ๆ 2-3 ประโยค "
                    f"เน้น insight ที่เป็นประโยชน์ต่อการตัดสินใจทางธุรกิจ "
                    f"เช่น แนวโน้ม จุดเด่น หรือข้อสังเกตสำคัญ"
                )
                raw = vn.submit_prompt(prompt=insight_prompt)
                analysis = raw.strip() if raw else None
                print(f"DEBUG: Storytelling generated: {analysis[:80] if analysis else 'None'}...")
        except Exception as insight_err:
            print(f"WARNING: Storytelling generation failed (non-fatal): {insight_err}")
            analysis = None

        return {
            "type": "data",
            "message": "วิเคราะห์ข้อมูลเรียบร้อยครับ",
            "analysis": analysis,
            "chart": chart_json,
            "sql": sql,
            "data": data,
        }
    except Exception as e:
        print(f"ERROR: Data query failed: {e}")
        return {
            "type": "error",
            "message": f"ขออภัย เกิดข้อผิดพลาดในการประมวลผลคำถาม: {str(e)}",
            "sql": None,
            "data": None,
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
        return []
    # Convert DataFrame to list of dicts
    return df.to_dict(orient='records')
