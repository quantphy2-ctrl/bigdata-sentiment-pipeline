
import csv
import json
import time
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data" / "processed" / "airline_ml"

TRAIN_PATH = DATA_DIR / "train.csv"
VAL_PATH = DATA_DIR / "validation.csv"

REPORT_PATH = (
    ROOT / "docs" / "reports"
    / "w04_ml_baseline_validation.json"
)

LABELS = ["negative", "neutral", "positive"]


# ==========================================
# 1. DOC DU LIEU
# ==========================================

def load_data(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Khong tim thay file: {path}"
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


X_train, y_train = load_data(TRAIN_PATH)
X_val, y_val = load_data(VAL_PATH)

print("\n=== W04: MACHINE LEARNING BASELINE ===")

print(f"Train records: {len(X_train):,}")
print(f"Validation records: {len(X_val):,}")

if len(X_train) != 10081 or len(X_val) != 2160:
    raise ValueError("So ban ghi khong dung ky vong")

if set(y_train) != set(LABELS):
    raise ValueError("Train khong du ba nhan")

if set(y_val) != set(LABELS):
    raise ValueError("Validation khong du ba nhan")


# ==========================================
# 2. TAO PIPELINE MACHINE LEARNING
# ==========================================

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
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        )
    )
])


# ==========================================
# 3. HUAN LUYEN TREN TAP TRAIN
# ==========================================

print("\n=== BAT DAU HUAN LUYEN ===")

start = time.perf_counter()

model.fit(X_train, y_train)

training_seconds = time.perf_counter() - start

print("PASS: Huan luyen hoan thanh")
print(f"Training time: {training_seconds:.3f} seconds")

feature_count = len(
    model.named_steps["tfidf"].get_feature_names_out()
)

print(f"TF-IDF features: {feature_count:,}")


# ==========================================
# 4. DU DOAN TREN TAP VALIDATION
# ==========================================

print("\n=== DU DOAN TREN VALIDATION ===")

y_pred = model.predict(X_val)

accuracy = accuracy_score(y_val, y_pred)

macro_f1 = f1_score(
    y_val,
    y_pred,
    labels=LABELS,
    average="macro",
    zero_division=0
)

print(f"Accuracy: {accuracy:.4f}")
print(f"Macro-F1: {macro_f1:.4f}")


# ==========================================
# 5. BAO CAO TUNG NHAN
# ==========================================

print("\n=== CLASSIFICATION REPORT ===")

print(
    classification_report(
        y_val,
        y_pred,
        labels=LABELS,
        digits=4,
        zero_division=0
    )
)


# ==========================================
# 6. CONFUSION MATRIX
# ==========================================

print("\n=== CONFUSION MATRIX ===")
print("Thu tu nhan: negative, neutral, positive")

cm = confusion_matrix(
    y_val,
    y_pred,
    labels=LABELS
)

for label, row in zip(LABELS, cm):
    print(f"{label}: {row.tolist()}")

print("Hang = nhan thuc te")
print("Cot = nhan du doan")


# ==========================================
# 7. LUU KET QUA VALIDATION
# ==========================================

report = {
    "model": "TF-IDF + Logistic Regression",
    "model_stage": "baseline",
    "training_records": len(X_train),
    "validation_records": len(X_val),
    "test_used": False,
    "tfidf": {
        "ngram_range": [1, 2],
        "min_df": 2,
        "max_features": 30000,
        "sublinear_tf": True,
        "actual_features": feature_count
    },
    "classifier": {
        "type": "LogisticRegression",
        "max_iter": 1000,
        "class_weight": "balanced",
        "random_state": 42
    },
    "training_seconds": round(
        training_seconds, 3
    ),
    "validation_accuracy": float(accuracy),
    "validation_macro_f1": float(macro_f1),
    "labels": LABELS,
    "confusion_matrix": cm.tolist(),
    "classification_report": classification_report(
        y_val,
        y_pred,
        labels=LABELS,
        output_dict=True,
        zero_division=0
    )
}

REPORT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

with REPORT_PATH.open("w", encoding="utf-8") as f:
    json.dump(
        report,
        f,
        indent=2,
        ensure_ascii=False
    )

print("\n=== HOAN THANH ===")
print(f"Da luu bao cao: {REPORT_PATH}")
print("Tap Test chua duoc su dung")
