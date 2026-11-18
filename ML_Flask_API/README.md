# California Housing Flask Prediction API

A small Flask REST API that serves the Random Forest regressor from the existing
California housing project. The API accepts either an ordered feature array or
an object keyed by feature name. A trained model is included as `model.joblib`.

The model predicts California district median house value in units of 100,000
USD (for example, `2.5` represents approximately $250,000). This is a dataset
demonstration, not a valuation service.

## Project layout

```text
ML_Flask_API/
  app.py
  config.py
  model.joblib
  train_model.py
  requirements.txt
  README.md
  utils/
    __init__.py
    model_loader.py
    preprocessing.py
    validation.py
  tests/
    test_api.py
```

## Setup and run locally

Run these commands from the `ML_Flask_API` directory. Python 3.10 or later is
recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

The API listens on `http://127.0.0.1:5000` by default. To regenerate the
demonstration model (the California housing dataset may need to be downloaded):

```powershell
python train_model.py
```

To load a different compatible sklearn model, set `MODEL_PATH` to its Joblib
file. The replacement model must accept the same eight features in the order
below, or expose a matching `feature_names_in_` attribute.

## Endpoints

### `GET /`

```json
{
  "status": "success",
  "message": "House price API is running."
}
```

### `GET /health`

```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### `POST /predict`

Use `Content-Type: application/json`. The model's feature order is:

1. `MedInc`
2. `HouseAge`
3. `AveRooms`
4. `AveBedrms`
5. `Population`
6. `AveOccup`
7. `Latitude`
8. `Longitude`

Array request:

```json
{
  "features": [8.3, 21, 6.9, 1.1, 320, 3.2, 37.8, -122.4]
}
```

Named request (keys must match all feature names exactly):

```json
{
  "features": {
    "MedInc": 8.3,
    "HouseAge": 21,
    "AveRooms": 6.9,
    "AveBedrms": 1.1,
    "Population": 320,
    "AveOccup": 3.2,
    "Latitude": 37.8,
    "Longitude": -122.4
  }
}
```

Successful response:

```json
{
  "status": "success",
  "prediction": 2.5,
  "prediction_unit": "100,000 USD"
}
```

This is a regressor and does not provide classification confidence scores.
Invalid requests return JSON with a suitable HTTP status, such as `400` for
malformed data and `415` when the request is not JSON:

```json
{
  "status": "error",
  "error": {
    "code": "bad_request",
    "message": "Expected 8 features in this order: MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup, Latitude, Longitude."
  }
}
```

## Test with Postman

1. Start the server with `python app.py`.
2. Create a request to `http://127.0.0.1:5000/health`, select **GET**, and
   choose **Send**. Expect HTTP `200` and `model_loaded: true`.
3. Create a request to `http://127.0.0.1:5000/predict`, select **POST**.
4. Under **Headers**, set `Content-Type` to `application/json`.
5. Under **Body**, select **raw** and choose **JSON**. Paste the array request
   above and choose **Send**. Expect HTTP `200` and a numeric prediction.
6. For error handling, remove the `features` property (expect `400`), send only
   three feature values (expect `400`), or change the body type to **Text**
   (expect `415`).

## Tests

```powershell
python -m pytest -q
```

The tests use a small in-memory test double and do not require downloading
training data.

## Configuration and deployment

Configuration is read from environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MODEL_PATH` | `model.joblib` in this directory | Model file to load |
| `HOST` | `127.0.0.1` | Bind address for the development server |
| `PORT` | `5000` | Port for the development server |
| `FLASK_DEBUG` | `0` | Enable the development debugger only for local work |
| `LOG_LEVEL` | `INFO` | Application log level |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated browser origins |

For production, deploy behind a TLS-terminating reverse proxy and use an
application server rather than Flask's development server. On Linux, from this
directory:

```bash
MODEL_PATH=/srv/house-api/model.joblib \
CORS_ORIGINS=https://your-frontend.example \
gunicorn --workers 2 --bind 0.0.0.0:8000 app:create_app()
```

Set environment variables through your hosting platform's secret/configuration
manager. Restrict CORS to trusted browser origins; CORS is not authentication.
Use HTTPS, authentication/authorization, request-size limits, rate limiting,
and network controls at the gateway or reverse proxy before exposing prediction
endpoints publicly. Keep the model file and dependencies trusted: Joblib files
use Python pickle serialization and must not be loaded from untrusted sources.
