# 08 — SECURITY

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. Overview

CIPHER-X is a local-first, offline-capable data processing pipeline. It does not expose a public API or process user-uploaded data in production. Security concerns are limited but still important.

---

## 2. Secrets & Credentials Management

### 2.1 Environment Variables

Any API keys (e.g., Copernicus SciHub login, Sentinel Hub API) MUST be stored in a `.env` file and NEVER committed to Git.

```bash
# .env (never commit this file)
COPERNICUS_USERNAME=your_username
COPERNICUS_PASSWORD=your_password
SENTINEL_HUB_CLIENT_ID=your_client_id
SENTINEL_HUB_CLIENT_SECRET=your_client_secret
```

Use `.env.example` as a template with placeholder values — this IS committed to Git.

### 2.2 .gitignore Rules

Ensure `.gitignore` includes:
```
.env
*.env
```

**Rule:** If `.env` is accidentally committed, rotate all credentials immediately.

---

## 3. Data Security

### 3.1 Satellite Data
- Sentinel-2 data is publicly available — no confidentiality requirement.
- Large raster files (`.tif`, `.jp2`) are excluded from Git via `.gitignore` to avoid accidental large-file commits and potential data leaks of pre-processed outputs.

### 3.2 AOI Sensitivity
- If the AOI represents a sensitive location (e.g., defence area), ensure `data/aoi/` is also excluded from Git.
- Add `data/aoi/` to `.gitignore` if needed.

---

## 4. Streamlit Dashboard Security

For the MVP, the dashboard runs locally (`localhost`). If deployed:

- Do **not** expose the Streamlit app on a public port without authentication.
- Use `streamlit run app/main.py --server.address localhost` for local-only binding.
- Do not log raw satellite data paths or credentials in Streamlit UI.

---

## 5. Dependency Security

- Pin exact dependency versions in `requirements.txt` for the demo to avoid supply-chain issues.
- Use only well-known PyPI packages (numpy, rasterio, scikit-image, etc.).
- Do not install packages from untrusted sources during the hackathon.

---

## 6. File Path Safety

All file paths in the code use `pathlib.Path` and are constructed from a project root variable:

```python
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]  # project root
```

**Never** use `os.system()` or `subprocess` with user-provided strings.  
**Never** pass unsanitized file paths to shell commands.

---

## 7. Checklist Before Demo

- [ ] `.env` is NOT in `git status` or `git log`
- [ ] No passwords hardcoded in any `.py` file
- [ ] `requirements.txt` uses known, trustworthy packages
- [ ] Streamlit app does not display raw filesystem paths to end users
- [ ] `data/sentinel/` is in `.gitignore`
