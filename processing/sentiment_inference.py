
import joblib

from functools import lru_cache
from pathlib import Path
from datetime import datetime, timezone

# ==========================================
# 1. CAU HINH MODEL
# ==========================================

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    ROOT
    / "models"
    / "airline_sentiment_v1.joblib"
)

MODEL_VERSION = "airline_sentiment_v1"


# ==========================================
# 2. TAI MODEL MOT LAN
# ==========================================

@lru_cache(maxsize=1)
def load_sentiment_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Khong tim thay model: {MODEL_PATH}"
        )

    # Chi tai model do project tu huan luyen.
    # Khong load file joblib tu nguon khong tin cay.
    model = joblib.load(MODEL_PATH)

    return model


# ==========================================
# 3. HAM DU DOAN DUNG CHUNG
# ==========================================

def predict_sentiments(texts):

    if not texts:
        return []

    # Khong du doan tren text rong.
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                "Moi ban ghi phai co text khong rong"
            )

    model = load_sentiment_model()

    probabilities = model.predict_proba(texts)

    classes = model.classes_

    predicted_indices = probabilities.argmax(axis=1)

    processed_at = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    results = []

    for i, class_index in enumerate(predicted_indices):

        label = str(classes[class_index])

        confidence = float(
            probabilities[i, class_index]
        )

        results.append({
            "sentiment_label": label,
            "sentiment_confidence": confidence,
            "processed_at": processed_at
        })

    return results


# ==========================================
# 4. CHAY THU DOC LAP
# ==========================================

if __name__ == "__main__":

    print("\n=== SHARED SENTIMENT INFERENCE ===")

    print(f"Model version: {MODEL_VERSION}")

    examples = [
        "The flight was fantastic and the crew was friendly.",
        "My flight was cancelled and I am angry.",
        "The airline released its updated schedule today."
    ]

    predictions = predict_sentiments(examples)

    for text, result in zip(examples, predictions):

        print("\n--------------------------------")

        print(f"Text: {text}")

        print(
            f"Sentiment: "
            f"{result['sentiment_label']}"
        )

        print(
            f"Confidence: "
            f"{result['sentiment_confidence']:.4f}"
        )

        print(
            f"Processed at: "
            f"{result['processed_at']}"
        )

    print("\nPASS: Shared inference hoat dong")
