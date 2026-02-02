import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error
import joblib

data_path = r"data/feature_data.csv"

df = pd.read_csv(data_path)

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

features = ["lag_1", "lag_7", "lag_14", "rolling_mean_7", "rolling_std_7", "day_of_week", "month"]

x = df[features]
y = df["qty_sold"]

split_date = df["date"].quantile(0.8)

x_train = x[df["date"] <= split_date]
y_train = y[df["date"] <= split_date]

x_test = x[df["date"] > split_date]
y_test = y[df["date"] > split_date]

baseline_pred = x_test["lag_1"]
baseline_mae = mean_absolute_error(y_test, baseline_pred)

model = LGBMRegressor(n_estimators=200, learning_rate=0.05)

model.fit(x_train, y_train)

preds = model.predict(x_test)

model_mae = mean_absolute_error(y_test, preds)

joblib.dump(model, r"data/forecast_model.pkl")

print("baseline_mae:", baseline_mae)
print("model_mae:", model_mae)
