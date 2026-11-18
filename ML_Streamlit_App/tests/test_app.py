from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_streamlit_app_loads():
    app_test = AppTest.from_file(str(PROJECT_DIR / "app.py")).run()

    assert not app_test.exception
    assert app_test.title[0].value == "House Price Prediction – Version 2"


def test_included_model_predicts_one_finite_value():
    model = joblib.load(PROJECT_DIR / "model.joblib")
    feature_names = list(model.feature_names_in_)
    features = pd.DataFrame(
        [[8.3, 21, 6.9, 1.1, 320, 3.2, 37.8, -122.4]],
        columns=feature_names,
    )

    prediction = model.predict(features)

    assert prediction.shape == (1,)
    assert np.isfinite(prediction[0])
