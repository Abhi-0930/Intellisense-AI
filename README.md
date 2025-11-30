
# IntelliSense AI – Backend Setup Guide

This README explains how to set up and run the **IntelliSense AI backend** using **uv** for dependency management.

---

## 🚀 Project Setup

### 1. **Clone the Repository**
```bash
git clone https://github.com/chandankumar123456/intellisense-ai.git
cd intellisense-ai
```

---

## 📦 Dependency Management with `uv`

This project uses **uv** for fast dependency installation and reproducible environments.

### 2. **Install Dependencies**
Just run:

```bash
uv sync
```

`uv sync` will:

- Create a virtual environment (if missing)
- Install dependencies listed in `requirements.txt`
- Apply versions locked in `uv.lock`
- Remove unused packages from the environment
- Ensure your environment exactly matches the project lockfile

That's all the user needs.

---

## ▶️ Running the Backend

Once dependencies are installed, run:

```bash
uv run uvicorn main:app --reload
```

or using Python directly:

```bash
python -m uvicorn main:app --reload
```

---

## 📁 Project Structure
```
IntelliSense-AI/
│── main.py
│── requirements.txt
│── uv.lock
│── README.md
└── ...
```

---

## 🔧 Adding New Packages

To add a new package:

```bash
uv add package-name
```

To add all packages inside `requirements.txt`:

```bash
uv add -r requirements.txt
```

After adding packages to the lockfile, update environment:

```bash
uv sync
```

---

## 👥 For Contributors

Anyone cloning your repo only needs to run:

```bash
uv sync
```

No manual venv creation, no pip install commands.

---

## ❓ Need Help?

Open an issue or ping the maintainer.

---
