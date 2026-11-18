import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.datasets import fetch_california_housing
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from config import PROJECT_DIR


def train_and_save(output_path):
    dataset = fetch_california_housing()
    features = pd.DataFrame(dataset.data, columns=dataset.feature_names)
    target = pd.Series(dataset.target)
    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    print("R2 score:", r2_score(y_test, predictions))
    print("RMSE:", mse**0.5)
    print("MAE:", mean_absolute_error(y_test, predictions))

    destination = Path(output_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, destination, compress=3)
    print("Saved model to:", destination)
    return model


def main():
    parser = argparse.ArgumentParser(
        description="Train the California housing demonstration model."
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_DIR / "model.joblib"),
        help="Path for the generated Joblib model.",
    )
    args = parser.parse_args()
    train_and_save(args.output)


if __name__ == "__main__":
    main()
