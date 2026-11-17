
import csv
import json
import time
from pathlib import Path

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data" / "processed" / "airline_ml"

REPORT_PATH = (
    ROOT / "docs" / "reports"
    / "w04_ml_model_comparison.json"
)

LABELS = ["negative", "neutral", "positive"]


# ==========================================
# 1. DOC TAP TRAIN VA VALIDATION
# ==========================================

def load_dataset(filename):
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Khong tim thay: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as f:
        rows = list(csv.DictReader(f))

    texts = [row["text"] for row in rows]
    labels = [
        row["airline_sentiment"]
        for row in rows
    ]

    return texts, labels


X_train, y_train = load_dataset("train.csv")
X_val, y_val = load_dataset("validation.csv")

print("\n=== W04: SO SANH CAU HINH ML ===")
print(f"Train: {len(X_train):,}")
print(f"Validation: {len(X_val):,}")
print("Test: CHUA SU DUNG")

# ==========================================
# 2. DINH NGHIA CAU HINH
# ==========================================

CONFIGS = [
    {
        "name": "baseline",
        "C": 1.0,
        "class_weight": "balanced"
    },
    {
        "name": "balanced_C_0.5",
        "C": 0.5,
        "class_weight": "balanced"
    },
    {
        "name": "balanced_C_2",
        "C": 2.0,
        "class_weight": "balanced"
    },
    {
        "name": "unweighted_C_1",
        "C": 1.0,
        "class_weight": None
    }
]

results = []

# ==========================================
# 3. HUAN LUYEN TUNG CAU HINH
# ==========================================

for config in CONFIGS:

    print(f"\n=== MODEL: {config['name']} ===")

    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=2,
                max_features=30000,
                sublinear_tf=True
            )
        ),
        (
            "classifier",
            LogisticRegression(
                C=config["C"],
                class_weight=config["class_weight"],
                max_iter=1000,
                random_state=42
            )
        )
    ])

    start = time.perf_counter()

    model.fit(X_train, y_train)

    training_seconds = (
        time.perf_counter() - start
    )

    predictions = model.predict(X_val)

    accuracy = accuracy_score(
        y_val, predictions
    )

    macro_f1 = f1_score(
        y_val,
        predictions,
        labels=LABELS,
        average="macro",
        zero_division=0
    )

    result = {
        "name": config["name"],
        "C": config["C"],
        "class_weight": config["class_weight"],
        "training_seconds": round(
            training_seconds, 3
        ),
        "accuracy": round(float(accuracy), 6),
        "macro_f1": round(float(macro_f1), 6),
        "classification_report": classification_report(
            y_val,
            predictions,
            labels=LABELS,
            output_dict=True,
            zero_division=0
        ),
        "confusion_matrix": confusion_matrix(
            y_val,
            predictions,
            labels=LABELS
        ).tolist()
    }

    results.append(result)

    print(f"Training: {training_seconds:.3f}s")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro-F1: {macro_f1:.4f}")

# ==========================================
# 4. CHON MO HINH TREN VALIDATION
# ==========================================

best = max(
    results,
    key=lambda r: (
        r["macro_f1"],
        r["accuracy"]
    )
)

print("\n=== BANG SO SANH ===")
print(
    f"{'Model':<22}"
    f"{'Accuracy':>12}"
    f"{'Macro-F1':>12}"
)

for result in results:
    print(
        f"{result['name']:<22}"
        f"{result['accuracy']:>12.4f}"
        f"{result['macro_f1']:>12.4f}"
    )

print("\n=== CAU HINH TOT NHAT TREN VALIDATION ===")
print(f"Model: {best['name']}")
print(f"Accuracy: {best['accuracy']:.4f}")
print(f"Macro-F1: {best['macro_f1']:.4f}")

print("\n=== CONFUSION MATRIX CUA MODEL TOT NHAT ===")
print("Labels: negative, neutral, positive")

for label, row in zip(
    LABELS,
    best["confusion_matrix"]
):
    print(f"{label}: {row}")

# ==========================================
# 5. LUU BAO CAO
# ==========================================

report = {
    "dataset": "Twitter US Airline Sentiment",
    "selection_metric": "validation_macro_f1",
    "train_records": len(X_train),
    "validation_records": len(X_val),
    "test_used": False,
    "tfidf": {
        "ngram_range": [1, 2],
        "min_df": 2,
        "max_features": 30000,
        "sublinear_tf": True
    },
    "models": results,
    "best_model_name": best["name"],
    "best_model_config": {
        "C": best["C"],
        "class_weight": best["class_weight"]
    }
}

REPORT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

with REPORT_PATH.open(
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        report,
        f,
        indent=2,
        ensure_ascii=False
    )

print("\n=== HOAN THANH ===")
print(f"Da luu bao cao: {REPORT_PATH}")
print("Tap Test van chua duoc su dung")
