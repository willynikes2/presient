
# 🤖 Presient AI Agent Developer Guide

Welcome, AI agent or junior contributor! This project is structured for modular, well-labeled development tasks. You can contribute feature-by-feature using the guide below.

---

## 🗂️ Project Structure

| Folder           | Purpose                               |
|------------------|----------------------------------------|
| `backend/`       | FastAPI backend code                  |
| `routes/`        | Individual API route files            |
| `models/`        | SQLAlchemy database models            |
| `schemas/`       | Pydantic validation for input/output  |
| `tests/`         | Unit + integration tests              |
| `firmware/`      | ESP32 code (coming soon)              |
| `frontend/`      | Mobile app (React Native)             |

---

## ⚙️ How to Run

```bash
cp backend/.env.example backend/.env
docker-compose up --build
```

API will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing

Write tests in `tests/` folder using `pytest`. Example:

```bash
pytest
```

---

## 🧠 Task Structure

Each GitHub Issue includes:
- 🎯 Goal
- 📂 Files to edit
- ✅ Test requirements

Use these to focus your work and test output before submitting a PR.

---

## ✅ Coding Style

- Use `snake_case` for variables
- Use `PascalCase` for class names
- Reuse database session via FastAPI dependency injection
- Lint code using `flake8`

---

## 📤 Submitting Work

1. Fork this repo
2. Create a branch: `feature/my-task-name`
3. Push changes
4. Submit PR and tag `@willynikes2` or use `ai-friendly` label
