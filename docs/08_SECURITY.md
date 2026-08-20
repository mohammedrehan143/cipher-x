# 08 — SECURITY

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20 (updated: BUG-03 fixed — `.env` now properly gitignored)

---

## 1. Overview

<<<<<<< HEAD
CIPHER-X is a local-first, offline-capable data processing pipeline. It does not expose a public API or process user-uploaded data in production. Security concerns are limited but still important for a hackathon team environment.
=======
CIPHER-X is an offline-capable, local-first data processing pipeline. It processes open-access satellite data and produces spatial vector and tabular outputs without exposing unauthenticated remote endpoints.
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213

---

## 2. Secrets & Credentials Management

### 2.1 Environment Variables
Any API keys or Copernicus credentials MUST be stored in `.env` and NEVER committed to version control.
Use `.env.example` as the committed template with placeholder values.

<<<<<<< HEAD
Any API keys (e.g., Copernicus SciHub login, Sentinel Hub API) MUST be stored in a `.env` file and NEVER committed to Git.

```bash
# .env  ← NEVER commit this file
COPERNICUS_USERNAME=your_username
COPERNICUS_PASSWORD=your_password
SENTINEL_HUB_CLIENT_ID=your_client_id
SENTINEL_HUB_CLIENT_SECRET=your_client_secret
```

Use `.env.example` as a template with placeholder values — this IS safe to commit.

### 2.2 .gitignore Rules (BUG-03 Fixed)

`.gitignore` now includes all `.env` variants:
```gitignore
.env
*.env
.env.*
!.env.example     ← this one IS committed (placeholder values only)
```

> **BUG-03 was fixed 2026-08-20:** `.env` was previously missing from `.gitignore`, creating a risk of accidentally committing credentials.

**Rule:** If `.env` is accidentally committed, rotate all credentials immediately:
```bash
git rm --cached .env
git commit -m "fix: remove .env from tracking"
# Then regenerate all credentials in the .env file
```
=======
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
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213

---

## 4. Dashboard & Web Security

<<<<<<< HEAD
### 3.1 Satellite Data
- Sentinel-2 data is publicly available — no confidentiality requirement for the data itself.
- Large raster files (`.tif`, `.jp2`) are excluded from Git via `.gitignore` to prevent accidental large-file commits.
- `outputs/*` is also gitignored (except `.gitkeep`) — generated outputs are not committed.

### 3.2 AOI Sensitivity
- If the AOI represents a sensitive location (e.g., a defence installation), ensure `data/aoi/` is also excluded from Git.
- Add `data/aoi/` to `.gitignore` if needed for your specific use case.
=======
- Run Streamlit locally: `streamlit run app/main.py --server.address localhost`
- Do not expose raw filesystem system paths or sensitive host environment information in user-facing dashboard components.
- Sanitize and validate file uploads if arbitrary AOIs are uploaded through the UI.
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213

---

## 5. File Path & Command Execution Safety

<<<<<<< HEAD
For the MVP, the dashboard runs locally (`localhost`). If deployed publicly:

- Do **not** expose the Streamlit app on a public port without authentication.
- Use `streamlit run app/main.py --server.address localhost` for local-only binding.
- Do not log raw satellite data paths or credentials anywhere in the Streamlit UI.
- Do not pass user-provided strings to `os.system()` or `subprocess`.

---

## 5. Dependency Security

- All packages in `requirements.txt` are well-known, trusted PyPI packages.
- Do not install packages from untrusted sources during the hackathon.
- After successful demo, pin exact versions via `pip freeze > requirements_frozen.txt` for reproducibility.

Current packages: `numpy, pandas, scikit-learn, scikit-image, scipy, matplotlib, opencv-python, rasterio, geopandas, shapely, pyproj, streamlit`

---

## 6. File Path Safety

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

## 7. Pre-Demo Security Checklist

- [ ] `git status` shows `.env` is NOT tracked
- [ ] `git log --all -- .env` returns empty (never committed)
- [ ] No passwords or API keys hardcoded in any `.py` file
- [ ] Streamlit app does not display raw filesystem paths to end users
- [ ] `data/sentinel/` and `data/processed/` are in `.gitignore`
- [ ] `requirements.txt` uses only known, trusted packages
=======
- All paths constructed using `pathlib.Path` rooted at the project directory.
- Avoid dynamic string concatenation in shell commands.
- Never use `os.system()` with raw user inputs.
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
