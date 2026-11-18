import logging
import math
import os
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st


FEATURE_NAMES = (
    "MedInc",
    "HouseAge",
    "AveRooms",
    "AveBedrms",
    "Population",
    "AveOccup",
    "Latitude",
    "Longitude",
)
DEFAULT_VALUES = (8.3, 21.0, 6.9, 1.1, 320.0, 3.2, 37.8, -122.4)
APP_VERSION = os.environ.get("APP_VERSION", "1.1.0")
MODEL_PATH = Path(
    os.environ.get("MODEL_PATH", str(Path(__file__).with_name("model.joblib")))
).expanduser()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@st.cache_resource
def load_model(path):
    model_file = Path(path)
    if not model_file.is_file():
        raise FileNotFoundError("Model file not found: {}".format(model_file))
    model = joblib.load(model_file)
    if not callable(getattr(model, "predict", None)):
        raise TypeError("The model must provide a callable predict method.")
    return model


def validate_features(values):
    if len(values) != len(FEATURE_NAMES):
        raise ValueError("Enter a value for each of the 8 model features.")

    for name, value in zip(FEATURE_NAMES, values):
        if not math.isfinite(value):
            raise ValueError("{} must be a finite number.".format(name))

    for name, value in zip(FEATURE_NAMES[:6], values[:6]):
        if value < 0:
            raise ValueError("{} cannot be negative.".format(name))

    latitude, longitude = values[6], values[7]
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90 degrees.")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180 degrees.")


st.set_page_config(
    page_title="California Housing Predictor",
    page_icon="🏠",
    layout="centered",
)
st.title("California Housing Price Predictor")
st.caption("Application version: {}".format(APP_VERSION))
st.write(
    "Enter the characteristics of a California district to estimate its "
    "median house value."
)
st.caption(
    "This demonstration model was trained on the California Housing dataset. "
    "Predictions are estimates, not financial advice."
)

try:
    model = load_model(str(MODEL_PATH))
except Exception:
    logger.exception("Could not load the prediction model")
    st.error(
        "The model could not be loaded. Check that the configured model file "
        "exists and is compatible with the installed scikit-learn version."
    )
    st.stop()

with st.form("prediction_form"):
    left, right = st.columns(2)
    values = []
    labels = (
        "Median income (MedInc)",
        "House age in years (HouseAge)",
        "Average rooms (AveRooms)",
        "Average bedrooms (AveBedrms)",
        "District population (Population)",
        "Average occupancy (AveOccup)",
        "Latitude",
        "Longitude",
    )

    for index, (name, label, default) in enumerate(
        zip(FEATURE_NAMES, labels, DEFAULT_VALUES)
    ):
        column = left if index % 2 == 0 else right
        if name == "Latitude":
            value = column.number_input(
                label,
                min_value=-90.0,
                max_value=90.0,
                value=default,
                step=0.1,
            )
        elif name == "Longitude":
            value = column.number_input(
                label,
                min_value=-180.0,
                max_value=180.0,
                value=default,
                step=0.1,
            )
        else:
            value = column.number_input(
                label,
                min_value=0.0,
                value=default,
                step=0.1,
            )
        values.append(value)

    submitted = st.form_submit_button("Predict median house value", type="primary")

if submitted:
    try:
        validate_features(values)
        model_input = pd.DataFrame([values], columns=FEATURE_NAMES)
        prediction = model.predict(model_input)
        if len(prediction) != 1:
            raise ValueError("The model returned an unexpected number of results.")

        result = prediction[0]
        st.subheader("Prediction")
        if callable(getattr(model, "predict_proba", None)):
            probabilities = model.predict_proba(model_input)[0]
            class_index = int(probabilities.argmax())
            classes = getattr(model, "classes_", None)
            predicted_class = classes[class_index] if classes is not None else result
            st.metric("Predicted class", str(predicted_class))
            st.metric("Confidence", "{:.1%}".format(float(probabilities[class_index])))
        else:
            numeric_result = float(result)
            if not math.isfinite(numeric_result):
                raise ValueError("The model returned a non-finite prediction.")
            st.metric(
                "Estimated median house value",
                "${:,.0f}".format(numeric_result * 100_000),
            )
            st.caption(
                "Model output: {:.4f} (units of $100,000). "
                "This regression model does not provide a confidence score."
                .format(numeric_result)
            )
    except (TypeError, ValueError) as error:
        st.error("Unable to make a prediction: {}".format(error))
    except Exception:
        logger.exception("Prediction failed")
        st.error("Prediction failed due to an unexpected error. Check the application logs.")
