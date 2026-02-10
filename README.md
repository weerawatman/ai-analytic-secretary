<div align="center">

# Executive AI Cockpit

### AI Analytic Secretary

**A privacy-first, self-hosted AI analytics platform that enables executives to query enterprise data using natural language.**

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14.2-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Docker](https://img.shields.io/badge/Docker_Compose-3.8-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Qwen_2.5-000000?style=for-the-badge&logo=ollama&logoColor=white)
![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)

</div>

---

## Overview

**Executive AI Cockpit** is a fully containerized AI analytics platform designed for business executives who need data insights without writing SQL. The system connects to your Google BigQuery data warehouse and translates plain English questions into optimized SQL queries — all powered by a locally running LLM.

Ask questions like *"What were our top 5 revenue sources last quarter?"* and receive instant, accurate answers. All conversation history and schema context are stored in a RAG-enabled PostgreSQL database with pgvector, allowing the system to improve its accuracy over time.

### Why Local-First?

- **Zero data leakage** — The LLM runs entirely on your infrastructure via Ollama. No API calls to external AI providers.
- **Full auditability** — Every query, response, and SQL statement is logged in your own database.
- **Compliance-friendly** — Meets strict data residency requirements since nothing leaves your network.

---

## Architecture

![Architecture Diagram](docs/images/architecture-diagram.png)

```
                    ┌──────────────────┐
                    │   Executive UI   │
                    │  (Next.js :3000) │
                    └────────┬─────────┘
                             │  HTTP
                             ▼
                    ┌──────────────────┐
                    │   Backend API    │
                    │ (FastAPI :8000)  │
                    │   + Vanna.ai     │
                    └──┬──────┬─────┬──┘
                       │      │     │
              ┌────────┘      │     └────────┐
              ▼               ▼              ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │   Ollama    │  │ PostgreSQL  │  │  BigQuery   │
     │ Qwen 2.5   │  │ + pgvector  │  │ (External)  │
     │  (:11434)   │  │  (:5432)    │  │             │
     └─────────────┘  └─────────────┘  └─────────────┘
      Local LLM        RAG Memory      Data Warehouse
      Inference        & Vector Store   (Read-Only)
```

### Data Flow

1. Executive types a natural language question in the dashboard
2. Frontend sends the question to the FastAPI backend via `POST /api/chat`
3. Backend passes the question to **Vanna.ai**, which uses the local **Ollama** LLM (Qwen 2.5 14B) to generate an optimized SQL query
4. The generated SQL is executed against **Google BigQuery** (read-only access)
5. Results are returned to the dashboard and the query is stored in **PostgreSQL + pgvector** for RAG memory

---

## Key Features

| Feature | Description |
|---|---|
| **Natural Language to SQL** | Powered by [Vanna.ai](https://vanna.ai/) — translates plain English questions into optimized BigQuery SQL using a local LLM. |
| **100% Local LLM** | Ollama runs the Qwen 2.5 14B model entirely on-premise. No data is sent to external AI services. |
| **RAG Memory** | PostgreSQL with pgvector stores past queries and schema context as vector embeddings, improving SQL generation accuracy over time. |
| **Executive Dashboard** | Dark glassmorphism UI built with Next.js 14, React 18, and Tailwind CSS — designed for clarity and speed. |
| **Single-Command Deployment** | `docker compose up -d` launches the entire 4-service stack with zero manual configuration. |
| **BigQuery Integration** | Secure, read-only access to Google BigQuery via service account credentials. |
| **Interactive API Docs** | Built-in Swagger UI at `/docs` for API exploration and testing. |

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js 14.2, React 18.3, Tailwind CSS 3.4, TypeScript 5 | Executive dashboard & chat interface |
| **Backend** | Python 3.10, FastAPI, Uvicorn | REST API & AI orchestration |
| **Text-to-SQL** | Vanna.ai 0.7.9 | Natural language to SQL translation |
| **LLM Runtime** | Ollama (Qwen 2.5 14B) | Local large language model inference |
| **AI Framework** | LangChain, Sentence Transformers | Embedding generation & AI pipeline |
| **Database** | PostgreSQL 16 + pgvector | RAG vector store, session memory, system data |
| **Data Warehouse** | Google BigQuery | Enterprise data source (read-only) |
| **Infrastructure** | Docker Compose 3.8 | Multi-service container orchestration |

---

## Prerequisites

| Requirement | Details |
|---|---|
| **Docker Desktop** | v4.x or later — [Download](https://www.docker.com/products/docker-desktop/) |
| **Memory** | 16 GB RAM minimum (the 14B model is memory-intensive) |
| **GPU** *(optional)* | NVIDIA GPU with CUDA support for faster LLM inference |
| **GCP Credentials** | Google Cloud service account JSON key with BigQuery read access |

> **Note:** The system runs on CPU-only machines, but LLM inference will be significantly slower without GPU acceleration.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ai-analytic-secretary.git
cd ai-analytic-secretary
```

### 2. Add GCP Credentials

Place your Google Cloud service account JSON file in the backend directory:

```bash
cp /path/to/your/service-account.json ./backend/gcp-service-account.json
```

> This file is excluded from version control via `.gitignore`.

### 3. Configure Environment Variables *(optional)*

Default values work out of the box. To customize, edit the `.env` file in the project root:

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_DB=ai_cockpit
```

### 4. Enable GPU Acceleration *(optional)*

If you have an NVIDIA GPU, uncomment the GPU section in `docker-compose.yml` under the `ollama` service:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### 5. Launch the Stack

```bash
docker compose up -d
```

This starts four containers:

| Container | Service | Port |
|---|---|---|
| `ai_cockpit_ui` | Next.js Frontend | `3000` |
| `ai_cockpit_api` | FastAPI Backend | `8000` |
| `ai_cockpit_db` | PostgreSQL + pgvector | `5432` |
| `ai_cockpit_brain` | Ollama LLM | `11434` |

### 6. Pull the LLM Model *(first run only)*

```bash
docker exec -it ai_cockpit_brain ollama pull qwen2.5:14b
```

> This download is approximately **9 GB** and only needs to be done once. The model is persisted in the `ollama_data/` volume.

---

## Usage

### Accessing the Application

| Service | URL |
|---|---|
| **Dashboard** | [http://localhost:3000](http://localhost:3000) |
| **API** | [http://localhost:8000](http://localhost:8000) |
| **API Docs (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) |

### Asking Questions

1. Open the dashboard at **http://localhost:3000**
2. Type a natural language question in the chat input:
   - *"Show me total revenue by region for Q4 2024"*
   - *"Who are our top 10 customers by order count?"*
   - *"Compare monthly sales between 2023 and 2024"*
   - *"What is the average order value by product category?"*
3. The AI generates SQL, executes it against BigQuery, and returns the results

### API Reference

#### Health Check

```
GET /
```

Returns the service status and active model name.

#### Chat Endpoint

```
POST /api/chat
Content-Type: application/json

{
  "question": "What were our top 5 revenue sources last quarter?"
}
```

Returns the AI-generated answer and the SQL query used.

---

## Project Structure

```
ai-analytic-secretary/
├── backend/                    # FastAPI backend service
│   ├── main.py                 # API endpoints, Vanna.ai configuration
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Backend container image
├── frontend/                   # Next.js frontend service
│   ├── src/
│   │   └── app/
│   │       ├── page.tsx        # Main chat interface component
│   │       ├── layout.tsx      # Root layout & metadata
│   │       └── globals.css     # Dark theme & glassmorphism styles
│   ├── package.json            # Node.js dependencies
│   ├── tailwind.config.ts      # Tailwind CSS configuration
│   ├── next.config.mjs         # Next.js standalone build config
│   └── Dockerfile              # Multi-stage frontend container image
├── docs/                       # Documentation assets
│   ├── images/
│   │   └── architecture-diagram.png
│   └── architecture-source.html
├── docker-compose.yml          # Service orchestration (4 services)
├── .env                        # Environment variables
├── .gitignore                  # Git exclusions
├── ollama_data/                # Persisted LLM model data (git-ignored)
├── pgdata/                     # Persisted PostgreSQL data (git-ignored)
└── README.md
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| **LLM responses are slow** | Enable GPU acceleration (see step 4) or use a smaller model variant. |
| **Backend fails to start** | Ensure the `db` and `ollama` containers are running: `docker compose ps`. |
| **BigQuery authentication error** | Verify `gcp-service-account.json` exists in `./backend/` and has BigQuery read permissions. |
| **Out of memory** | The 14B model requires at least 16 GB RAM. Close other applications or use a smaller model. |
| **Model not found** | Run `docker exec -it ai_cockpit_brain ollama pull qwen2.5:14b` to download the model. |

---

## Security Considerations

- **Local LLM inference** — No enterprise data is sent to third-party AI providers.
- **Read-only data access** — BigQuery is accessed through a service account scoped to read-only permissions.
- **Credential isolation** — Service account keys are mounted as Docker volumes and excluded from version control.
- **Network isolation** — All inter-service communication occurs within the Docker internal network.
- **Environment variables** — Sensitive configuration is managed through `.env` files, not hardcoded.

---

## License

This project is proprietary. All rights reserved.

---

<div align="center">

**Built with local-first AI principles. Your data stays yours.**

</div>
