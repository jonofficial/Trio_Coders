# Enterprise Resource Management Agents

This repository contains two distinct, high-impact enterprise agentic solutions designed to optimize Resource Management processes:

1. **Fresher Deployment Agent (FDA)**: An AI-Driven Workforce Pyramid Optimization & Analytics Platform.
2. **Incorrect Allocation Identifier (IAI - Agent 01)**: An automated analytics and monitoring system for identifying resource allocation and task exceptions.

Both agents leverage modern technology stacks (Python/FastAPI backends, React/Vite frontends) to transform manual spreadsheet operations into automated, deterministic, and insightful dashboard-driven processes.

---

## 1. Fresher Deployment Agent (FDA)
*An AI-Driven Workforce Pyramid Optimization & Analytics Platform*

### 📝 Overview
FDA bridges the gap between raw HR data and actionable resource management. It automatically evaluates IT projects against an optimal workforce pyramid (79% Junior, 20% Mid, 1% Senior). When deviations or "top-heavy" structures are detected, FDA leverages LangGraph workflows and generative AI to provide prescriptive deployment strategies, calculating exact fresher intake numbers, and generating tailored training curriculums. This ensures that entry-level talent is deployed exactly where needed with the correct skill preparations.

### 🛠️ Tech Stack
- **Backend:** Python, FastAPI, LangGraph, Groq (Llama-3.1-8B), Pandas, openpyxl.
- **Frontend:** React 19, Vite, TailwindCSS v4, Recharts, SheetJS (xlsx).

### 🚦 Running FDA Locally

**Prerequisites:** Node.js (v18+), Python (3.10+).

**1. Backend Setup**
```bash
cd Fresher_Deployment_Agent/backend
python -m venv .venv
# Activate the environment:
# Windows: .\.venv\Scripts\Activate.ps1
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```
*Create a `.env` file in `Fresher_Deployment_Agent/backend/` and add your Groq API key (a fallback key is provided in the repository).*
```env
GROQ_API_KEY=your_groq_api_key_here
```
*Start the FastAPI server:*
```bash
python main.py
# Server runs on http://127.0.0.1:8000
```

**2. Frontend Setup**
```bash
# In a new terminal
cd Fresher_Deployment_Agent/frontend
npm install
echo "VITE_BACKEND_URL=http://127.0.0.1:8000" > .env
npm run dev
# Dashboard runs on http://localhost:5173
```

---

## 2. Incorrect Allocation Identifier (IAI)
*Automated Analytics & Monitoring System for Resource Allocation*

### 📝 Overview
IAI replaces manual cross-referencing processes for IT service resource allocations. It ingests massive datasets from Resource Information Systems (RIS) and Staffing Orders (SO) and applies complex business rules to identify critical data integrity issues and billing exceptions. The system automatically flags scenarios such as stale long leaves, contractors inappropriately on the bench, task type mismatches, and over/under allocations. It produces rigorous audit trails, exception reports, and a real-time tracking dashboard for Resource Managers.

### 🛠️ Tech Stack
- **Backend:** Python 3.10+, FastAPI, SQLAlchemy, PostgreSQL, Pandas.
- **Frontend:** React 18, Vite, Recharts, Vanilla CSS (Enterprise Dark Theme).

### 🚦 Running IAI Locally

**Prerequisites:** Node.js (v16+), Python (3.10+), PostgreSQL (running on `localhost:5432`).

**1. Database Setup**
Ensure your local PostgreSQL service is running. Create a database named `iai_db`:
```sql
CREATE DATABASE iai_db;
```

**2. Backend Setup**
```bash
cd Incorrect_Allocation_Identifier/backend
python -m venv .venv
# Activate the environment:
# Windows: .\.venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```
*Create a `.env` file in `Incorrect_Allocation_Identifier/` with:*
```env
DATABASE_URL=<your-database-connection-string>
PSID_FIELD_NAME=<your-identifier-field>
RM_NOTIFICATION_URL=<your-webhook-url>
OUTPUT_DIR=<path-to-data-directory>
LOG_LEVEL=INFO
```
*Start the server:*
```bash
python -m uvicorn main:app --reload
# Server runs on http://127.0.0.1:8000
```

**3. Frontend Setup**
```bash
# In a new terminal
cd Incorrect_Allocation_Identifier/frontend
npm install
npm run dev
# Dashboard runs on http://localhost:5173
```

---

## 📁 Repository Structure
```text
Trio_Coders/
├── Fresher_Deployment_Agent/         # Agent for optimizing Fresher Pyramids
│   ├── backend/                      # FastAPI & LangGraph logic
│   ├── frontend/                     # React dashboard
│   ├── data/                         # Synthetic input data
│   └── output/                       # Generated analysis reports
├── Incorrect_Allocation_Identifier/  # Agent for flagging allocation rule violations
│   ├── backend/                      # FastAPI, Pandas rules engine, PostgreSQL schema
│   ├── frontend/                     # React monitoring dashboard
│   └── Data/                         # Input and Config datasets
└── README.md                         # This file
```
