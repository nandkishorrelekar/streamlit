from pathlib import Path

import joblib


def load_model(model_path):
    path = Path(model_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(
            "Model file not found at {!s}. Train one with "
            "`python train_model.py` or set MODEL_PATH.".format(path)
        )

    model = joblib.load(path)
    if not callable(getattr(model, "predict", None)):
        raise TypeError("The loaded model must provide a callable predict method.")
    return model
