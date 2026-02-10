from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import html
import os
import re
import json
import warnings
import pandas as pd
from vanna.ollama import Ollama
from vanna.pgvector import PG_VectorStore
from google.cloud import bigquery

warnings.filterwarnings("ignore")

# --- Configuration ---
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://admin:admin@db:5432/ai_cockpit')
MODEL_NAME = 'qwen2.5:7b'
ANALYSIS_TIMEOUT = 10  # seconds — skip AI tasks if they take longer

# --- Custom Vanna Class ---
class MyVanna(Ollama, PG_VectorStore):
    def __init__(self, config=None):
        Ollama.__init__(self, config=config)
        PG_VectorStore.__init__(self, config=config)

        # Define initial_prompt ONCE — used by get_sql_prompt below
        self.initial_prompt = (
            "You are a SQL expert that generates BigQuery-compatible SQL. "
            "CRITICAL RULE: STRICTLY use English snake_case for ALL SQL column aliases "
            "(e.g., use `total_revenue` NOT `ยอดขาย`, use `customer_name` NOT `ชื่อลูกค้า`). "
            "NEVER use Thai, Chinese, or any non-ASCII characters in SQL aliases, column names, "
            "or table aliases. This is mandatory to prevent JSON parsing errors."
        )

        try:
            self.bq_client = bigquery.Client.from_service_account_json('service_account.json')
        except Exception:
            self.bq_client = None

    def get_sql_prompt(self, initial_prompt=None, question="", question_sql_list=None, ddl_list=None, doc_list=None, **kwargs):
        """Always inject our own initial_prompt to prevent duplication."""
        return super().get_sql_prompt(
            initial_prompt=self.initial_prompt,
            question=question,
            question_sql_list=question_sql_list or [],
            ddl_list=ddl_list or [],
            doc_list=doc_list or [],
            **kwargs,
        )

    def run_sql(self, sql: str) -> pd.DataFrame:
        try:
            job = self.bq_client.query(sql)
            return job.to_dataframe()
        except Exception:
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

    # --- Chat / Greeting ---
    if intent == 'chat':
        message = generate_chat_response(question)
        return JSONResponse(content={
            "type": "chat",
            "message": message,
            "sql": None,
            "data": None,
            "analysis": None,
        })

    # --- Data Query ---
    try:
        sql = vn.generate_sql(question)
        df = vn.run_sql(sql)

        # ── Safety Layer: Sanitize column names ──
        # LLM may generate non-ASCII aliases (Thai/Chinese) that break the frontend.
        # Force-rename to safe English keys: label, label_2, ... / value, value_2, ...
        if df is not None and not df.empty:
            new_cols = []
            label_n = 0
            value_n = 0
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    value_n += 1
                    new_cols.append('value' if value_n == 1 else f'value_{value_n}')
                else:
                    label_n += 1
                    new_cols.append('label' if label_n == 1 else f'label_{label_n}')
            df.columns = new_cols

        data = []
        if df is not None and not df.empty:
            data = df.to_dict(orient='records')

        # ── Instant Insight (Pure Python — zero LLM latency) ──
        analysis = None
        if df is not None and not df.empty and 'value' in df.columns and 'label' in df.columns:
            try:
                top_record = df.sort_values(by='value', ascending=False).iloc[0]
                total_val = df['value'].sum()
                pct = (top_record['value'] / total_val * 100) if total_val > 0 else 0
                label_safe = html.escape(str(top_record['label']))
                analysis = (
                    f"จากการวิเคราะห์ข้อมูล พบว่า <b>{label_safe}</b> "
                    f"มียอดสูงสุดที่ <b>{top_record['value']:,.0f}</b> "
                    f"({pct:.1f}%)<br>"
                    f"ยอดรวมทั้งหมด: <b>{total_val:,.0f}</b>"
                )
            except Exception:
                pass

        # Serialize with default=str to handle datetime/Decimal from BigQuery
        response_data = json.loads(json.dumps({
            "type": "data",
            "message": "Analysis complete.",
            "sql": sql,
            "data": data,
            "analysis": analysis,
        }, default=str))

        return JSONResponse(content=response_data)

    except Exception as e:
        return JSONResponse(content={
            "type": "error",
            "message": f"Error processing query: {str(e)}",
            "sql": None,
            "data": None,
            "analysis": None,
        })

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
