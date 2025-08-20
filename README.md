# blueQuery_backend 🧠🔍

blueQuery_backend is a prototype backend system designed to convert natural language queries into precise SQL statements that retrieve information from the CCTNS 2.0 database—India’s official police records system. This project demonstrates how large-scale structured data can be queried intelligently using self-hosted AI models and schema-aware reasoning agents.

## 🧠 Purpose

The core objective is to enable seamless access to law enforcement data through natural language. Users can ask questions in plain English (or other supported languages), and the system generates accurate SQL queries to fetch relevant results from the Oracle-based CCTNS 2.0 database.

This prototype is under internal evaluation for CCTNS-based workflows and is built with scalability in mind. It can be extended into a production-grade backend service.

## 🧠 Architecture Highlights

- 🔍 Converts natural language input into SQL queries
- 🧠 Uses self-hosted LLMs (no external APIs)
- 🗃️ Connects directly to OracleDB (CCTNS 2.0)
- 🧠 Employs schema-aware agents and reasoning modules
- 🧠 RAG pipeline powered by ChromaDB (not SQLite)

## 🧠 Model Infrastructure

- 🧠 Self-hosted Qwen 32B model
- 🧠 Self-hosted Ollama 3.3 (70B)
- ❌ No external LLM APIs (e.g., OpenAI, Gemini)
- ✅ Fully offline, secure, and reproducible

## 🗂️ Data Handling

- ✅ Real data from OracleDB (CCTNS 2.0)
- 📊 16 relational tables with 1,000+ rows and columns
- ❌ No mock data used
- ❌ No external GitHub repos for hosting or testing
- ❌ No blob storage required — data is already provisioned

## 🔧 Features

- 🧠 Natural language to SQL conversion
- 🗃️ Schema validation and health checks
- 🔍 Retrieval-Augmented Generation (RAG) with ChromaDB
- 🧱 Modular agent architecture
- 🔐 Secure, offline inference pipeline

## 🚀 Getting Started

1. Clone the repo and install dependencies:

```bash
pip install -r requirements.txt
```
2. Start the backend server:
```
python main.py
```

3. Ensure OracleDB connection is configured in ```config.py```.

🛠️ Tech Stack
Python 3.10+
ChromaDB for vector search
OracleDB for structured data
Self-hosted LLMs (Qwen 32B, Ollama 70B)
FastAPI (planned)



🤝 Contributing
Pull requests are welcome! If you have ideas for improving schema handling, agent logic, or model orchestration, feel free to fork the repo and submit changes.

📄 License
This project is currently unlicensed. Please check back for updates.
