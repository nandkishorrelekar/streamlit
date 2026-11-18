import logging
import time

import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, HTTPException, UnsupportedMediaType

from config import Config
from utils.model_loader import load_model
from utils.preprocessing import to_model_input
from utils.validation import validate_features


def create_app(config_override=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_override:
        app.config.update(config_override)

    logging.basicConfig(
        level=getattr(logging, str(app.config["LOG_LEVEL"]).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    app.logger.setLevel(
        getattr(logging, str(app.config["LOG_LEVEL"]).upper(), logging.INFO)
    )

    model = app.config.get("MODEL")
    if model is None:
        model = load_model(app.config["MODEL_PATH"])
    if not callable(getattr(model, "predict", None)):
        raise TypeError("The configured model must provide a callable predict method.")

    feature_names = tuple(
        str(name)
        for name in getattr(model, "feature_names_in_", Config.DEFAULT_FEATURE_NAMES)
    )
    app.config["MODEL"] = model
    app.config["FEATURE_NAMES"] = feature_names

    origins = app.config["CORS_ORIGINS"]
    if isinstance(origins, str):
        origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
    CORS(app, resources={r"/*": {"origins": list(origins)}})

    @app.before_request
    def start_request_timer():
        request.start_time = time.perf_counter()

    @app.after_request
    def log_request(response):
        duration_ms = (time.perf_counter() - request.start_time) * 1000
        app.logger.info(
            "%s %s %s %.2fms",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        app.logger.warning("HTTP %s: %s", error.code, error.description)
        return (
            jsonify(
                {
                    "status": "error",
                    "error": {
                        "code": error.name.lower().replace(" ", "_"),
                        "message": error.description,
                    },
                }
            ),
            error.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unhandled API error")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": {
                        "code": "internal_server_error",
                        "message": "An unexpected error occurred.",
                    },
                }
            ),
            500,
        )

    @app.get("/")
    def index():
        return jsonify({"status": "success", "message": "House price API is running."})

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy", "model_loaded": True})

    @app.post("/predict")
    def predict():
        if not request.is_json:
            raise UnsupportedMediaType(
                description="Content-Type must be application/json."
            )

        payload = request.get_json()
        try:
            values = validate_features(payload, app.config["FEATURE_NAMES"])
        except ValueError as error:
            raise BadRequest(description=str(error)) from error

        model_input = to_model_input(values, app.config["FEATURE_NAMES"])
        predictions = np.asarray(app.config["MODEL"].predict(model_input)).reshape(-1)
        if predictions.size != 1 or not np.isfinite(predictions[0]):
            raise RuntimeError("The model returned an invalid prediction.")

        return jsonify(
            {
                "status": "success",
                "prediction": float(predictions[0]),
                "prediction_unit": "100,000 USD",
            }
        )

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host=application.config["HOST"],
        port=application.config["PORT"],
        debug=application.config["DEBUG"],
    )
