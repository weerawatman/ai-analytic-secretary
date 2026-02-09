FROM python:3.10-slim

WORKDIR /app

# 1. ลงโปรแกรมพื้นฐานที่จำเป็นสำหรับ compile (กันเหนียว)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 2. ลง libraries ปกติ
RUN pip install --no-cache-dir -r requirements.txt

# 3. [ไม้ตาย] บังคับลง Vanna ซ้ำแบบระบุเจาะจง (ใส่ฟันหนู "..." เพื่อล็อควงเล็บไม่ให้หลุด)
RUN pip install --no-cache-dir --force-reinstall "vanna[postgres,ollama]==0.7.9"

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]