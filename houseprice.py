
import mlflow
import mlflow.sklearn
import pandas as pd

from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score
)

data = fetch_california_housing()

X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(data.target)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

mlflow.set_experiment("House_Price_Prediction")

models = {
    "Linear_Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("model", LinearRegression())
    ]),

    "Decision_Tree": DecisionTreeRegressor(
        max_depth=10,
        random_state=42
    ),

    "Random_Forest": RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
}

results = []

best_r2 = float("-inf")
best_model_name = None
best_run_id = None

for model_name, model in models.items():

    with mlflow.start_run(run_name=model_name) as run:

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        mse = mean_squared_error(y_test, y_pred)
        rmse = mse ** 0.5
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        mlflow.log_param("model_name", model_name)

        mlflow.log_metric("MSE", mse)
        mlflow.log_metric("RMSE", rmse)
        mlflow.log_metric("MAE", mae)
        mlflow.log_metric("R2_Score", r2)

        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            skops_trusted_types=[
                "sklearn.tree._tree.Tree"
            ]
        )

        results.append({
            "Model": model_name,
            "MSE": mse,
            "RMSE": rmse,
            "MAE": mae,
            "R2_Score": r2
        })

        print("\nModel:", model_name)
        print("MSE:", mse)
        print("RMSE:", rmse)
        print("MAE:", mae)
        print("R2 Score:", r2)

        if r2 > best_r2:
            best_r2 = r2
            best_model_name = model_name
            best_run_id = run.info.run_id

results_df = pd.DataFrame(results)

print("\n========== MODEL COMPARISON ==========")
print(results_df.to_string(index=False))

print("\n========== BEST MODEL ==========")
print("Model:", best_model_name)
print("R2 Score:", best_r2)

model_name = "Best_House_Price_Predictor"

model_uri = f"runs:/{best_run_id}/model"

registered_model = mlflow.register_model(
    model_uri=model_uri,
    name=model_name
)

print("\n========== MODEL REGISTRY ==========")
print("Model Name:", model_name)
print("Model Version:", registered_model.version)

loaded_model = mlflow.sklearn.load_model(
    f"models:/{model_name}/{registered_model.version}"
)

predictions = loaded_model.predict(X_test)

print("\n========== ACTUAL HOUSE PRICES ==========")
print(y_test[:10].values)

print("\n========== PREDICTED HOUSE PRICES ==========")
print(predictions[:10])

print("\nHOUSE PRICE PREDICTION COMPLETED SUCCESSFULLY")
