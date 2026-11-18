import numpy as np
import pytest

from app import create_app
from config import Config


class StubRegressor:
    feature_names_in_ = Config.DEFAULT_FEATURE_NAMES

    def predict(self, features):
        return np.array([2.5])


@pytest.fixture
def client():
    app = create_app(
        {
            "TESTING": True,
            "MODEL": StubRegressor(),
            "CORS_ORIGINS": [],
        }
    )
    return app.test_client()


def test_root_and_health(client):
    root = client.get("/")
    health = client.get("/health")

    assert root.status_code == 200
    assert root.get_json()["status"] == "success"
    assert health.status_code == 200
    assert health.get_json() == {"status": "healthy", "model_loaded": True}


def test_valid_prediction_with_ordered_features(client):
    response = client.post(
        "/predict",
        json={"features": [8.3, 21, 6.9, 1.1, 320, 3.2, 37.8, -122.4]},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "success",
        "prediction": 2.5,
        "prediction_unit": "100,000 USD",
    }


def test_valid_prediction_with_named_features(client):
    feature_names = Config.DEFAULT_FEATURE_NAMES
    response = client.post(
        "/predict",
        json={"features": dict.fromkeys(feature_names, 1.0)},
    )

    assert response.status_code == 200


def test_missing_features_returns_400(client):
    response = client.post("/predict", json={})

    assert response.status_code == 400
    assert response.get_json()["error"]["message"] == "Missing required field: features."


def test_invalid_json_returns_json_400(client):
    response = client.post(
        "/predict",
        data='{"features":',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "bad_request"


def test_incorrect_feature_count_returns_400(client):
    response = client.post("/predict", json={"features": [1, 2, 3]})

    assert response.status_code == 400
    assert "Expected 8 features" in response.get_json()["error"]["message"]


def test_non_numeric_feature_returns_400(client):
    response = client.post(
        "/predict",
        json={"features": [1, 2, 3, 4, 5, 6, 7, "not-a-number"]},
    )

    assert response.status_code == 400
    assert "must be a JSON number" in response.get_json()["error"]["message"]


def test_non_json_content_type_returns_415(client):
    response = client.post("/predict", data="{}", content_type="text/plain")

    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "unsupported_media_type"


def test_unexpected_prediction_error_returns_generic_500(client, monkeypatch):
    def fail_prediction(_features):
        raise RuntimeError("internal detail")

    monkeypatch.setattr(
        client.application.config["MODEL"], "predict", fail_prediction
    )
    response = client.post("/predict", json={"features": [1] * 8})

    assert response.status_code == 500
    assert response.get_json()["error"] == {
        "code": "internal_server_error",
        "message": "An unexpected error occurred.",
    }
    assert "internal detail" not in response.get_data(as_text=True)
