import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent


class Config:
    MODEL_PATH = os.environ.get(
        "MODEL_PATH", str(PROJECT_DIR / "model.joblib")
    )
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DEBUG = os.environ.get("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    CORS_ORIGINS = tuple(
        origin.strip()
        for origin in os.environ.get(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origin.strip()
    )
    DEFAULT_FEATURE_NAMES = (
        "MedInc",
        "HouseAge",
        "AveRooms",
        "AveBedrms",
        "Population",
        "AveOccup",
        "Latitude",
        "Longitude",
    )
