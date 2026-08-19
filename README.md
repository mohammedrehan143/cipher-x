# Cipher-X

Satellite-based change detection system (formerly Human Change Detection).

## Project Structure

```
cipher-x/
├── data/                # Datasets (raw & processed)
│   └── README.md
├── src/                 # Source code
│   ├── preprocessing/   # Data loading & cleaning
│   ├── cva/             # Change Vector Analysis
│   ├── liss4/           # LISS-IV imagery processing
│   ├── model/           # Model definitions & training
│   └── utils/           # Shared utilities
├── notebooks/           # Jupyter notebooks for exploration
├── outputs/             # Generated results & visualizations
├── models/              # Saved model weights
├── app/                 # Application entry points
├── requirements.txt
└── .gitignore
```

## Setup

```bash
pip install -r requirements.txt
```

## License

See [LICENSE](LICENSE).
