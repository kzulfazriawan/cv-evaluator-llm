# CV Evaluator LLM

A Django Rest Framework (DRF) backend service to evaluate a candidate’s CV and project report using a real LLM (via OpenRouter).

---

## Features
- Upload CV + project report (PDF/DOCX/TXT)
- Async evaluation with background threads
- LLM scoring & feedback in structured JSON
- Validation & error handling (timeouts, retries, rate limits)
- SQLite database (lightweight for demo)

---

## Setup

1. Clone repo & create virtual environment:
   ```bash
   git clone https://github.com/yourusername/ai-cv-evaluator.git
   cd ai-cv-evaluator
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Copy .env.example to .env
   ```bash
   cp .env.example .env
   ```

4. Edit the .env with your configuration API keys and model

5. Load superuser (Optional)
   ```bash
   python manage.py loaddata fixtures/superuser.yaml
   ```

6. Start serer
   ```bash
   python manage.py runserver
   ```

List of Endpoints:

- POST /upload
- POST /evaluate
- GET /result/{id}