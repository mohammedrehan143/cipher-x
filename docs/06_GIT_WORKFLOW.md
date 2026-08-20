# 06 — GIT WORKFLOW

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. Branch Strategy

```
main
└── dev
    ├── feature/person1-preprocessing-cva
    ├── feature/person2-vectorization-features
    ├── feature/person3-ml-classification
    └── feature/person4-dashboard
```

| Branch | Purpose | Owner |
|---|---|---|
| `main` | Stable, demo-ready code only. Protected. | Team |
| `dev` | Integration branch. Merge module features here first. | Team |
| `feature/person1-*` | Sentinel-2 ingestion, preprocessing, CVA | Person 1 |
| `feature/person2-*` | Mask vectorization, NDVI, feature extraction | Person 2 |
| `feature/person3-*` | Labeller, Random Forest classifier, inference runner | Person 3 |
| `feature/person4-*` | Streamlit interactive GIS dashboard | Person 4 |

**Rule:** Never commit directly to `main`. Always merge via `dev` first.

---

## 2. Commit Convention

Format:
```
<type>(<scope>): <short description>

[optional body]
```

| Type | When to use |
|---|---|
| `feat` | New feature or module |
| `fix` | Bug fix |
| `refactor` | Code restructure, no behaviour change |
| `docs` | Documentation updates |
| `test` | Tests added or verified |
| `chore` | Dependency update, folder configuration |

**Examples:**
```
feat(preprocessing): add Sentinel-2 band loader with reflectance scaling
feat(vectorization): add polygonize with morphological noise removal
feat(models): add RandomForestClassifier with balanced class weighting
feat(app): add interactive map with category filtering
```

---

## 3. What NOT to Commit

See `.gitignore`. Critical exclusions:

```
*.tif  *.tiff  *.jp2       # Large raster data files
data/sentinel/             # Raw Sentinel-2 downloads
data/processed/            # Intermediate rasters
outputs/*                  # Generated outputs (except .gitkeep)
.env                       # Secrets / API keys
.venv/  __pycache__/       # Python environment
```

---

## 4. Emergency Recovery

```bash
# Undo last commit (keep changes staged)
git reset --soft HEAD~1

# Discard local changes to a file
git checkout -- src/models/classifier.py

# View status & history
git status
git log --oneline -10
```
