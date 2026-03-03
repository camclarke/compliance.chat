# Compliance.chat

A multi-agent RAG (Retrieval-Augmented Generation) system designed to scrape, process, and query comprehensive global product compliance documents. The system acts as a single pane of glass for requirements across:
- **Telecommunications** (e.g., FCC, IFETEL)
- **Electrical Safety** (e.g., UL, CE, NOM)
- **Energy Efficiency**
- **Medical Devices** (e.g., FDA, MDR)
- **Battery Regulations**
- **Environmental Compliance** (e.g., RoHS, REACH, WEEE)
- **Textile Labeling**

> **Hackathon MVP Scope:** To deliver a highly polished, functional prototype within the time constraints, the current MVP rollout focuses specifically on the **LATAM region**, featuring an extensive, robust ingestion pipeline for **Mexican NOMs** (Normas Oficiales Mexicanas).

## Project Architecture

The project is composed of three main components:

### 1. Data Ingestion Crawler (`/data_ingestion_crawler`)
A set of Python scripts responsible for fetching and indexing compliance data.
- **Extraction**: Uses `PyPDFLoader` to extract text from regulatory documents.
- **Embedding & Indexing**: Uses the local `all-MiniLM-L6-v2` HuggingFace model via Langchain to generate semantic embeddings efficiently and at zero cost. The chunked data is stored in a persistent local **ChromaDB** vector database.

### 2. Backend API (`/backend`)
A **FastAPI** application serving as the core engine for the multi-agent RAG system.
- Integrates with **Semantic Kernel** powered by **Azure OpenAI** for sophisticated multi-agent reasoning, tool calling, and response generation.
- Connects to the local ChromaDB populated by the crawler to retrieve relevant document chunks during RAG workflows.
- Exposes REST endpoints (e.g., `/api/chat`) for the frontend to communicate with the AI agents.

### 3. Frontend Application (`/frontend`)
A modern Single Page Application built with **React** and **Vite**.
- Provides a chat interface for users to interact with the compliance knowledge base.
- Secures access using Microsoft Authentication Library (**MSAL**).

## Setup & Local Development

### Prerequisites
- Node.js (v18+)
- Python 3.10+
- Azure OpenAI API key and endpoint
- (Optional) Microsoft Entra ID (Status: configured for MSAL Auth)

### 1. Environment Variables
Create a `.env` file in the `backend/` directory with your Azure OpenAI credentials. These are used by both the backend and the data ingestion crawler.
```env
AZURE_OPENAI_ENDPOINT="your-endpoint-url"
AZURE_OPENAI_API_KEY="your-api-key"
```

### 2. Data Ingestion (ChromaDB Generation)
The vector database containing the compliance documents (e.g., Mexican regulations) is located at `backend/data/chroma_db`. 

If you need to re-run the crawler or ingest new data:
```bash
cd data_ingestion_crawler
pip install -r ../backend/requirements.txt # Or create a dedicated venv
python crawler.py
```

### 3. Running the Backend
1. Open a new terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 4. Running the Frontend
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
The frontend should now be running and accessible typically at `http://localhost:5173`, communicating with the FastAPI backend on `http://localhost:8000`.
