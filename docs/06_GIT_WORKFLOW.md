# 06 — GIT WORKFLOW

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. Branch Strategy

```
main
└── dev
    ├── feature/person1-preprocessing
    ├── feature/person1-cva
    ├── feature/person2-vectorization
    ├── feature/person2-features
    ├── feature/person2-ml
    └── feature/person2-dashboard
```

| Branch | Purpose |
|---|---|
| `main` | Stable, demo-ready code only. Protected. |
| `dev` | Integration branch. Merge features here first. |
| `feature/person1-*` | Person 1 work branches |
| `feature/person2-*` | Person 2 work branches |

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
| `docs` | Documentation only |
| `test` | Tests added/updated |
| `chore` | Dependency update, folder creation |
| `wip` | Work in progress (do not merge to main) |

**Examples:**
```
feat(preprocessing): add band loader with reflectance scaling
fix(cva): handle NaN in magnitude when all pixels masked
docs(api): add function signatures to 04_API_DOCUMENTATION.md
chore(deps): add scikit-image and scipy to requirements.txt
```

---

## 3. Day-of-Hackathon Workflow

```
# 1. Start your feature branch
git checkout dev
git pull origin dev
git checkout -b feature/person1-preprocessing

# 2. Work, commit often
git add src/preprocessing/loader.py
git commit -m "feat(preprocessing): add load_bands function"

# 3. Push your branch
git push origin feature/person1-preprocessing

# 4. When done with a module, merge to dev
git checkout dev
git merge feature/person1-preprocessing
git push origin dev

# 5. Final integration — merge dev to main
git checkout main
git merge dev
git push origin main
```

---

## 4. Pull Request Rules

- Title must follow commit convention
- At minimum, the other team member must review before merge to `main`
- For hackathon speed: self-merge to `dev` is allowed, but `main` merges need a second eye

---

## 5. What NOT to Commit

See `.gitignore`. Critical exclusions:

```
*.tif  *.tiff  *.jp2       # Large raster data files
data/sentinel/             # Raw Sentinel-2 downloads
data/processed/            # Intermediate rasters
outputs/*                  # Generated outputs (except .gitkeep)
models/*.pt  *.h5          # Trained model weights
.env                       # Secrets / API keys
venv/  __pycache__/        # Python environment
```

---

## 6. Tags & Releases

```bash
# Tag the demo-ready commit
git tag -a v1.0-demo -m "SIH 2026 demo submission"
git push origin v1.0-demo
```

---

## 7. Emergency Recovery

```bash
# Undo last commit (keep changes staged)
git reset --soft HEAD~1

# Discard local changes to a file
git checkout -- src/preprocessing/loader.py

# See what changed
git diff HEAD
git log --oneline -10
```
