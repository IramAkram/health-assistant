# Agentic AI-Powered Smart Health Monitoring & Personal Healthcare Assistant

Final Year Project – web app built with **FastAPI + PostgreSQL/SQLAlchemy + scikit-learn + OpenAI Agents SDK + Plotly + ReportLab**.

> Informational wellness tool. It does **not** diagnose disease, prescribe medication or make emergency decisions.

## Quick start (VS Code)

```bash
# 1. open this folder in VS Code  (File > Open Folder)
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env   (then edit SECRET_KEY)

uvicorn app.main:app --reload
```
Open **http://127.0.0.1:8000** (app) or **http://127.0.0.1:8000/docs** (interactive API docs).

Optional extras:
```bash
python scripts/seed_demo_data.py     # demo user: demo@example.com / Demo@12345 (30 days of data)
python scripts/create_admin.py admin@example.com "Admin@12345"
pytest                               # run tests
```
The `.env` defaults to **SQLite** so it works immediately. To use **PostgreSQL** (as in the proposal):
`docker compose up -d`, then set `DATABASE_URL=postgresql+psycopg2://health_user:health_pass@localhost:5432/health_db`.

Press **F5** in VS Code to run/debug the server (`.vscode/launch.json` included).

## AI assistant modes
* **With `OPENAI_API_KEY` in `.env`** → real multi-agent system (OpenAI Agents SDK).
* **Without a key** → offline *demo mode* with keyword routing to the same tools, so everything still works for demos.

## Project structure
```
app/
  main.py, config.py, database.py, models.py, schemas.py, security.py, deps.py
  routers/        auth, records, dashboard(+risk), alerts(+reminders), assistant, reports, admin
  services/       alert_rules (deterministic), analysis (pandas), ml_service, report_service (PDF), tools (agent tools)
  ai_agents/      specialists.py (Coordinator + 4 agents), fallback.py (demo mode), runner.py
ml/               generate_synthetic_dataset.py, train_diabetes.py, models/ (trained model + metrics.json)
data/diabetes.csv dataset used for training
frontend/         index.html (login/register), dashboard.html, css/, js/app.js
scripts/          create_admin.py, seed_demo_data.py
tests/            test_core.py (pure logic), test_api.py (end-to-end)
docs/             Project_Proposal.pdf
```

## How it maps to the proposal
| Proposal module | Where |
|---|---|
| Registration / profile (JWT) | `routers/auth.py`, `security.py` |
| Health data entry + validation | `routers/records.py`, `schemas.py` |
| Data analysis | `services/analysis.py` |
| ML risk estimation (LogReg / Decision Tree / Random Forest) | `ml/train_diabetes.py`, `services/ml_service.py` |
| Coordinator + 4 agents | `ai_agents/specialists.py` |
| Alerts & reminders (rule-based) | `services/alert_rules.py`, `routers/alerts.py` |
| Dashboard & charts (Plotly) | `routers/dashboard.py`, `frontend/js/app.js` |
| PDF report (ReportLab) | `services/report_service.py`, `routers/reports.py` |
| Administration | `routers/admin.py` |

Safety design: agents never touch the DB – they call permission-checked functions in `services/tools.py`, which always use the user id from the JWT (never from the LLM). Critical alerts come only from `alert_rules.py`.

## Datasets
`data/diabetes.csv` currently holds a **synthetic** dataset in the Pima format (768 rows, same columns) so the project runs offline. **For your report/viva, use the real dataset:**
1. Download **Pima Indians Diabetes Database** – Kaggle (`uciml/pima-indians-diabetes-database`) or UCI/NIDDK.
2. Save it as `data/diabetes.csv` (columns: Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age, Outcome).
3. Run `python ml/train_diabetes.py` – it compares the 3 models, saves the best to `ml/models/` and writes `metrics.json`.

The model uses 4 features the app can provide: Glucose, diastolic BP, BMI, Age. Note: Pima glucose is a lab (OGTT) value while users enter home readings – mention this as a limitation.

## Known limitations (state them in your report)
* Alert thresholds are general adult reference values – review with a medical source.
* The risk model is trained on a small dataset; it is an informational estimate only.
* Reminders notify only while the browser page is open (no email/SMS service).
