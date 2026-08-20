# 08 — SECURITY

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20 (Unified Security Standards)

---

## 1. Overview

CIPHER-X is an offline-capable, local-first data processing pipeline. It processes open-access satellite data and produces spatial vector and tabular outputs without exposing unauthenticated remote endpoints.

---

## 2. Secrets & Credentials Management

### 2.1 Environment Variables
Any API keys (e.g., Copernicus SciHub login, Sentinel Hub API) MUST be stored in `.env` and NEVER committed to version control.
Use `.env.example` as the committed template with placeholder values:

```bash
# .env  ← NEVER commit this file
COPERNICUS_USERNAME=your_username
COPERNICUS_PASSWORD=your_password
SENTINEL_HUB_CLIENT_ID=your_client_id
SENTINEL_HUB_CLIENT_SECRET=your_client_secret
```

### 2.2 .gitignore Rules (BUG-03 Fixed)
Verify that `.gitignore` contains:
```gitignore
.env
*.env
.env.*
!.env.example
data/sentinel/
outputs/
```

---

## 3. Machine Learning & Model Security

### 3.1 Model Deserialization Safety
- Use `joblib` for model loading from trusted project paths only (`models/rf_classifier.joblib`).
- Never load untrusted external `.pkl` or `.joblib` files from third-party URLs.
- Save model metadata (`rf_metadata.json`) in plain text JSON to allow transparent auditing of feature names, class mappings, and hyperparameters without executing pickled bytecode.

---

## 4. Dashboard & Web Security

- Run Streamlit locally: `streamlit run app/main.py --server.address localhost`
- Do not expose raw filesystem system paths or sensitive host environment information in user-facing dashboard components.
- Sanitize and validate file uploads if arbitrary AOIs are uploaded through the UI.

---

## 5. File Path & Command Execution Safety

All file paths in code use `pathlib.Path` and are constructed project-relative:

```python
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]  # navigate to project root
```

**Rules:**
- Never use `os.system()` or `subprocess` with user-provided path strings
- Never pass unsanitized filenames to shell commands
- Always use `Path.mkdir(parents=True, exist_ok=True)` before writing outputs

---

## 6. Pre-Demo Security Checklist

- [ ] `git status` shows `.env` is NOT tracked
- [ ] `git log --all -- .env` returns empty (never committed)
- [ ] No passwords or API keys hardcoded in any `.py` file
- [ ] Streamlit app does not display raw filesystem paths to end users
- [ ] `data/sentinel/` and `data/processed/` are in `.gitignore`
- [ ] `requirements.txt` uses only known, trusted packages
