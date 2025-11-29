# Intellisense-AI
🚀 IntelliSense AI

A modern FastAPI-based AI backend powered by uv, FastAPI, Python 3.11+, and clean project structure.

This document explains how to set up and run the project from scratch, even for someone opening the repo for the first time.

📦 1. Clone the Project
git clone https://github.com/chandankumar123456/intellisense-ai.git
cd intellisense-ai

🐍 2. Install uv (if not installed)

uv is a super-fast Python package manager + virtual environment system.

Install (recommended):

pip install uv


Check version:

uv --version

🧩 3. Install Dependencies

Inside the project root directory:

uv sync


This will:

Create a virtual environment at .venv

Install all dependencies from pyproject.toml

Lock versions for reproducibility

⚠️ Important Note

Do NOT activate conda or any other environment.

uv manages everything automatically.

▶️ 4. Run the Application (Recommended)

Use uv to run the FastAPI server correctly:

uv run uvicorn main:app --reload


This ensures:

Correct .venv is used

No Anaconda/conda conflicts

FastAPI + Pydantic v2 run smoothly

The server starts on:

http://127.0.0.1:8000

📌 5. Project Structure
IntelliSense AI/
│
├── main.py
├── pyproject.toml
├── uv.lock
├── README.md
└── app/
    ├── routers/
    ├── services/
    ├── utils/
    └── models/


(If your structure changes, update here.)

🧪 6. Testing the API

Open your browser:

http://127.0.0.1:8000/docs


FastAPI automatically generates Swagger UI.

🔄 7. Updating Dependencies

If you want to install a new package:

uv add package-name


Example:

uv add fastapi
uv add "openai>=1.0"

🛠️ 8. Running Any Python Script

To run any Python file inside the project:

uv run python filename.py

➕ 9. Removing and Rebuilding Environment

If anything breaks:

uv clean
uv sync


This rebuilds a clean environment.