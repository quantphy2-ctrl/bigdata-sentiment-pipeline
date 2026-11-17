
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
    / "w04_ml_final_test.json"
)

LABELS = ["negative", "neutral", "positive"]


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

    X = [row["text"] for row in rows]
    y = [row["airline_sentiment"] for row in rows]

    return X, y


# ==========================================
# 1. DOC TRAIN VA VALIDATION
# ==========================================

X_train, y_train = load_dataset("train.csv")
X_val, y_val = load_dataset("validation.csv")

X_fit = X_train + X_val
y_fit = y_train + y_val

print("\n=== W04: FINAL MODEL EVALUATION ===")
print(f"Train: {len(X_train):,}")
print(f"Validation: {len(X_val):,}")
print(f"Training combined: {len(X_fit):,}")

if len(X_fit) != 12241:
    raise ValueError(
        "So ban ghi Train + Validation khong dung"
    )

# ==========================================
# 2. CAU HINH DA CHON TREN VALIDATION
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
            C=2.0,
            class_weight="balanced",
            max_iter=1000,
            random_state=42
        )
    )
])

# ==========================================
# 3. HUAN LUYEN TREN TRAIN + VALIDATION
# ==========================================

print("\n=== HUAN LUYEN MO HINH CUOI ===")

start = time.perf_counter()

model.fit(X_fit, y_fit)

training_seconds = time.perf_counter() - start

print("PASS: Huan luyen hoan thanh")
print(f"Training time: {training_seconds:.3f}s")

feature_count = len(
    model.named_steps["tfidf"].get_feature_names_out()
)

print(f"TF-IDF features: {feature_count:,}")

# ==========================================
# 4. MO TAP TEST SAU KHI DA HUAN LUYEN
# ==========================================

print("\n=== DANH GIA TAP TEST ===")

X_test, y_test = load_dataset("test.csv")

print(f"Test records: {len(X_test):,}")

if len(X_test) != 2161:
    raise ValueError("So dong Test khong dung")

if not set(X_fit).isdisjoint(set(X_test)):
    raise RuntimeError(
        "Phat hien text trung giua training va Test"
    )

if set(y_test) != set(LABELS):
    raise ValueError("Test khong du ba nhan")

print("PASS: Khong trung text chinh xac voi Test")

# ==========================================
# 5. DU DOAN VA TINH METRICS
# ==========================================

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

macro_f1 = f1_score(
    y_test,
    y_pred,
    labels=LABELS,
    average="macro",
    zero_division=0
)

print("\n=== FINAL TEST RESULTS ===")

print(f"Accuracy: {accuracy:.4f}")
print(f"Macro-F1: {macro_f1:.4f}")

print("\n=== CLASSIFICATION REPORT ===")

print(
    classification_report(
        y_test,
        y_pred,
        labels=LABELS,
        digits=4,
        zero_division=0
    )
)

# ==========================================
# 6. CONFUSION MATRIX
# ==========================================

cm = confusion_matrix(
    y_test,
    y_pred,
    labels=LABELS
)

print("\n=== CONFUSION MATRIX ===")
print("Labels: negative, neutral, positive")

for label, row in zip(LABELS, cm):
    print(f"{label}: {row.tolist()}")

print("Hang = nhan thuc te")
print("Cot = nhan du doan")

# ==========================================
# 7. LUU BAO CAO KET QUA CUOI
# ==========================================

report = {
    "dataset": "Twitter US Airline Sentiment",
    "model": "TF-IDF + Logistic Regression",
    "model_config": {
        "C": 2.0,
        "class_weight": "balanced",
        "max_iter": 1000,
        "random_state": 42
    },
    "selected_using": "validation_macro_f1",
    "refit_on": "train_plus_validation",
    "train_records": len(X_train),
    "validation_records": len(X_val),
    "final_training_records": len(X_fit),
    "test_records": len(X_test),
    "tfidf_features": feature_count,
    "training_seconds": round(training_seconds, 3),
    "test_accuracy": float(accuracy),
    "test_macro_f1": float(macro_f1),
    "labels": LABELS,
    "confusion_matrix": cm.tolist(),
    "classification_report": classification_report(
        y_test,
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
print(f"Report: {REPORT_PATH}")
print("Final Test evaluation completed.")
