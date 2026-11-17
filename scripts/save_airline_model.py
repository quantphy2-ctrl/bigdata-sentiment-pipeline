
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import joblib
import sklearn

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data" / "processed" / "airline_ml"

MODEL_PATH = (
    ROOT / "models" / "airline_sentiment_v1.joblib"
)

REPORT_PATH = (
    ROOT / "docs" / "reports"
    / "w04_model_artifact.json"
)


# ==========================================
# 1. DOC TRAIN VA VALIDATION
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

X_fit = X_train + X_val
y_fit = y_train + y_val

print("\n=== W04: LUU MO HINH ML ===")
print(f"Training records: {len(X_fit):,}")

if len(X_fit) != 12241:
    raise ValueError("So dong huan luyen khong dung")


# ==========================================
# 2. CAU HINH DA CHOT
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
# 3. HUAN LUYEN LAI
# ==========================================

print("\n=== HUAN LUYEN TRAIN + VALIDATION ===")

model.fit(X_fit, y_fit)

feature_count = len(
    model.named_steps["tfidf"].get_feature_names_out()
)

print(f"TF-IDF features: {feature_count:,}")
print("PASS: Training completed")


# ==========================================
# 4. LUU MO HINH
# ==========================================

print("\n=== LUU MODEL JOBLIB ===")

MODEL_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

if MODEL_PATH.exists():
    raise FileExistsError(
        f"Model da ton tai: {MODEL_PATH}"
    )

joblib.dump(
    model,
    MODEL_PATH,
    compress=3
)

print(f"Saved model: {MODEL_PATH}")
print(
    f"Model size: "
    f"{MODEL_PATH.stat().st_size / 1048576:.2f} MiB"
)


# ==========================================
# 5. TAI LAI VA THU DU DOAN
# ==========================================

print("\n=== KIEM TRA MODEL DA LUU ===")

# Chi tai file joblib do chinh chuong trinh
# nay tao ra, khong tai file tu nguon la.
loaded_model = joblib.load(MODEL_PATH)

examples = [
    "The flight was fantastic and the crew was friendly.",
    "My flight was cancelled and I am angry.",
    "The airline released its updated schedule today."
]

predictions = loaded_model.predict(examples)
probabilities = loaded_model.predict_proba(examples)

for text, label, probs in zip(
    examples,
    predictions,
    probabilities
):
    confidence = float(max(probs))

    print(f"\nText: {text}")
    print(f"Predicted sentiment: {label}")
    print(f"Confidence score: {confidence:.4f}")

print("\nPASS: Model reloaded and predictions completed")


# ==========================================
# 6. LUU THONG TIN MODEL
# ==========================================

model_sha256 = hashlib.sha256(
    MODEL_PATH.read_bytes()
).hexdigest()

report = {
    "model_name": "airline_sentiment_v1",
    "model_type": "TF-IDF + Logistic Regression",
    "model_file": "models/airline_sentiment_v1.joblib",
    "trained_at_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "training_records": len(X_fit),
    "training_sources": [
        "train.csv",
        "validation.csv"
    ],
    "test_used": False,
    "C": 2.0,
    "class_weight": "balanced",
    "random_state": 42,
    "tfidf_features": feature_count,
    "labels": loaded_model.classes_.tolist(),
    "sklearn_version": sklearn.__version__,
    "model_sha256": model_sha256
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
print(f"Model: {MODEL_PATH}")
print(f"Report: {REPORT_PATH}")
