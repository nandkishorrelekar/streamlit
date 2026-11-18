import pandas as pd


def to_model_input(values, feature_names):
    return pd.DataFrame([values], columns=feature_names)
