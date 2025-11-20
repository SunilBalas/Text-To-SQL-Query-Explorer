# Text-To-SQL Query Explorer 

It is a **streamlit app** that converts plain English questions into SQL queries, executes them against a connected database (**SQLite** or **PostgreSQL**), and returns results. The project uses embeddings of database schema stored in FAISS to help the LLM (**Groq** / **LLaMa 3.2**) map natural language to the correct schema-aware SQL.

---

## Table of contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Architecture Overview](#architecture-overview)
4. [Project Demo](#project-demo)
5. [Prerequisites](#prerequisites)
6. [Quick Start (Development)](#quick-start-development)
7. [Configuration](#configuration)
8. [How it works (step-by-step)](#how-it-works-step-by-step)
9. [Running the App](#running-the-app)
10. [Contribution](#contribution)
11. [File Structure](#file-structure)
12. [Final Notes and Next Steps](#final-notes-and-next-steps)
---

## Features

- Connect to **SQLite** (upload `.db`) or **PostgreSQL** (connection config / secrets).
- Auto-extract table / column schema and generate schema embeddings.
- Store schema embeddings in a FAISS vector store (local file).
- Convert user natural language to SQL using Groq-backed LLaMa 3.2 (via LangChain/Groq adapter).
- Execute generated SQL against the connected DB and show results in the UI.
- Safety checks: preview SQL, explain query plan (optional), and guardrails for destructive statements.

---

## Tech Stack

- Python 3.12
- Streamlit (UI)
- LangChain (prompting + chains)
- Groq model runner (LLaMa 3.2)
- SentenceTransformers for embeddings
- FAISS vector store (local)
- sqlite3 & psycopg2 (PostgreSQL)

---

## Architecture Overview

1. **Streamlit UI** — handles DB connection, schema upload, query input, results display.
2. **Schema Extractor** — reads DB schema from SQLite file (`.db`) or PostgreSQL; builds human-readable `schema_text` for each table (table name, columns, types, sample rows if allowed).
3. **Embeddings** — `SentenceTransformer` converts schema snippets into vectors.
4. **FAISS** — stores vectors with metadata (table, column, foreign keys relationships). On app startup or after schema change the index is rebuilt or updated.
5. **LLM Layer (Groq / LLaMa)** — LangChain prompts the model with the user question + most relevant schema snippets (retrieved from FAISS) to produce a SQL query.
6. **SQL Executor** — validates and runs SQL on the connected DB and returns results to UI.

---

---

## Project Demo

https://github.com/user-attachments/assets/67b96ca2-a801-403e-ba56-1f52ea568dd9

https://github.com/user-attachments/assets/cf5c8758-73b7-4344-a367-41f724646c92

---

## Prerequisites

- Python 3.12 installed
- `pip` and `anaconda` environment  installed
- If using PostgreSQL: access + credentials + `psycopg2-binary`
- If using GPU inference for Groq/LLaMa you must configure the model runner accordingly (not covered here)

Recommended system (dev): 8+ GB RAM.

---

## Quick Start (Development)

1. Clone the repo:

```bash
git clone <your-repo-url>
cd Text-To-SQL-Query-Explorer
```

2. Create virtual environment & install dependencies:

```bash
# Windows
conda create --prefix=venv python=3.12 -y
conda activate ./venv

pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `secrets.toml` file under `.streamlit` folder and place your databases configuration, LLMs configurations, API secrets, etc., (DO NOT COMMIT IT!). Example `.secrets.toml`:

```
[postgres]
server = <SERVER NAME>
dbname = <DB NAME>
host = <HOST NAME>
port = <PORT>
user = <USER>
password = <PASSWORD>

[sqlite]
dbname = "" # if you want, you can pass DB name here...

[groq]
type = "groq"
model = <MODEL NAME>
api_key = <GROQ API KEY>
temperature = <TEMPERATURE>
max_tokens = <MAX TOKENS>

[faiss]
type = "faiss"
model = <MODEL NAME>
```

## How it works (step-by-step)

1. **Start app** — user opens Streamlit app in browser.
2. **Choose DB type** — SQLite (upload .db) or PostgreSQL (enter/choose connection using secrets).
3. **Schema extraction** — app reads table names, column names, types, nullable info, and optional sample rows (first N) to build a textual schema representation.
4. **Make embeddings** — each schema chunk (e.g., "table: orders — columns: id, user_id, amount, created_at") is embedded with SentenceTransformer.
5. **Save to FAISS** — embeddings + metadata saved to FAISS (file) for reuse.
6. **User query** — user types plain English question ("Show top 5 customers by purchase amount last month").
7. **Retrieve relevant schema** — app queries FAISS for nearest schema chunks to the question.
8. **Prompt construction** — combine user question + retrieved schema snippets + explicit instructions / safety constraints into a LangChain prompt template.
9. **LLM call** — send prompt to Groq (LLaMa) and receive SQL output.
10. **SQL safety & preview** — parse SQL to detect destructive commands (DROP, DELETE without WHERE, ALTER, etc). If flagged, show preview and ask for explicit confirmation.
11. **Execute** — run the SQL on the connected DB, return results and show query execution time and sample rows. Cache results if desired.

---

## Running the App

Development run:

```bash
streamlit run app.py
```

If `app.py` is the main Streamlit script, it will open at `http://localhost:8501` by default.

Deployment suggestions:

- For small apps: Streamlit Cloud, Render, or Heroku; make sure to provide secrets via platform UI.
- If you need to run the LLM externally (recommended for production), deploy Groq/Llama in a separate inference service and call it via API.

---

## Contribution

### Fork the Repository

Click the **Fork** button on GitHub to create your own copy.

### Clone Your Fork

```bash
git clone https://github.com/SunilBalas/Text-To-SQL-Query-Explorer.git
cd Text-To-SQL-Query-Explorer
```

### Create a Feature Branch

Use a meaningful branch name:

```bash
git checkout -b feature/<short-description>
```

Example:

```bash
git checkout -b feature/add-mysql-connector
```

### Make Your Changes

Modify or add new functionality.

### Stage and Commit Your Changes

```bash
git add .
git commit -m "Add: <your meaningful commit message>"
```

### Push Your Branch

```bash
git push origin feature/<short-description>
```

### Open a Pull Request

Go to your GitHub repository → **Compare & Pull Request**.

Please include:

* Clear description of changes
* Screenshots (if UI related)
* Related Issue reference (if applicable)
---

## File Structure

```
📦 Text-To-SQL-Query-Explorer
│
├── Core/
│   ├── Base/
│   ├── Enums/
│   ├── Factory/
│   ├── Repository/
│   │   ├── database.py
│   │   ├── llm_provider.py
│   │   └── vectorstore.py
│   └── Utils/
├── Data/
│   ├── Chunks/
│   ├── DBs/
│   └── Indexes/
├── Database/
├── LLM/
├── Logs/
├── VectorStore/
├── .env
├── .gitignore
├── app.dev.py
├── app.py
├── README.md
├── requirements.txt
└── setup.py

```
---

## Final Notes and Next Steps

- Consider adding an **explain** mode where the LLM provides a human-readable explanation of the generated SQL and the plan.
- Add an audit log for all generated SQL queries with timestamp and user id (if multi-user) for traceability.
- If you plan to support more DBs (MySQL, Snowflake), modularize the schema extractor and SQL executor.

---
