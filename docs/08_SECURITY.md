# 08 — SECURITY

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. Overview

CIPHER-X is an offline-capable, local-first data processing pipeline. It processes open-access satellite data and produces spatial vector and tabular outputs without exposing unauthenticated remote endpoints.

---

## 2. Secrets & Credentials Management

### 2.1 Environment Variables
Any API keys or Copernicus credentials MUST be stored in `.env` and NEVER committed to version control.
Use `.env.example` as the committed template with placeholder values.

### 2.2 .gitignore Verification
Verify that `.gitignore` contains:
```
.env
*.env
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

- All paths constructed using `pathlib.Path` rooted at the project directory.
- Avoid dynamic string concatenation in shell commands.
- Never use `os.system()` with raw user inputs.
