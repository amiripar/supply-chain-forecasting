import sqlite3
import pandas as pd
from datetime import timedelta
import joblib
import numpy as np

db_path = r"data/sc.db"
model_path = r"data/forecast_model.pkl"
horizon_days = 14
service_level_z = 1.65

def load_latest_snapshot():
    con = sqlite3.connect(db_path)
    orders = pd.read_sql("select * from orders_daily", con)
    inventory = pd.read_sql("select * from inventory_snapshot_daily", con)
    master = pd.read_sql("select * from master_data", con)
    con.close()

    orders["date"] = pd.to_datetime(orders["date"])
    inventory["date"] = pd.to_datetime(inventory["date"])

    last_date = orders["date"].max()

    inv_last = inventory[inventory["date"] == last_date].copy()
    return orders, inv_last, master, last_date

def build_future_features(orders, sku_id, location_id, last_date):
    s = orders[(orders["sku_id"] == sku_id) & (orders["location_id"] == location_id)].copy()
    s = s.sort_values("date")
    s = s.set_index("date")[["qty_sold"]]

    future_dates = [last_date + timedelta(days=i) for i in range(1, horizon_days + 1)]

    rows = []
    history = s["qty_sold"].copy()

    for d in future_dates:
        lag_1 = history.iloc[-1]
        lag_7 = history.iloc[-7] if len(history) >= 7 else history.iloc[0]
        lag_14 = history.iloc[-14] if len(history) >= 14 else history.iloc[0]
        rolling_mean_7 = history.iloc[-7:].mean() if len(history) >= 7 else history.mean()
        rolling_std_7 = history.iloc[-7:].std(ddof=0) if len(history) >= 7 else history.std(ddof=0)

        day_of_week = d.dayofweek
        month = d.month

        rows.append([d, lag_1, lag_7, lag_14, rolling_mean_7, rolling_std_7, day_of_week, month])

        history = pd.concat([history, pd.Series([np.nan], index=[d])])

    df_future = pd.DataFrame(
        rows,
        columns=["date", "lag_1", "lag_7", "lag_14", "rolling_mean_7", "rolling_std_7", "day_of_week", "month"]
    )
    return df_future

def forecast_series(model, df_future):
    features = ["lag_1", "lag_7", "lag_14", "rolling_mean_7", "rolling_std_7", "day_of_week", "month"]
    preds = model.predict(df_future[features])
    df_future["forecast_qty"] = np.maximum(0, np.round(preds)).astype(int)
    return df_future

def compute_inventory_actions(df_forecast, on_hand, lead_time_days):
    lead_time_days = int(lead_time_days)
    lead_time_days = max(1, min(lead_time_days, horizon_days))

    demand_lt = df_forecast["forecast_qty"].iloc[:lead_time_days]
    demand_mean = float(demand_lt.mean())
    demand_std = float(demand_lt.std(ddof=0))

    reorder_point = int(round(demand_mean * lead_time_days + service_level_z * demand_std * np.sqrt(lead_time_days)))

    demand_next_lt = int(demand_lt.sum())
    stockout_risk = int(on_hand) < demand_next_lt

    demand_horizon = int(df_forecast["forecast_qty"].sum())
    overstock_risk = int(on_hand) > int(round(demand_horizon * 1.5))

    return reorder_point, demand_next_lt, demand_horizon, stockout_risk, overstock_risk

def main():
    model = joblib.load(model_path)

    orders, inv_last, master, last_date = load_latest_snapshot()

    results = []
    for _, row in inv_last.iterrows():
        sku_id = row["sku_id"]
        location_id = row["location_id"]
        on_hand = int(row["on_hand"])

        md = master[(master["sku_id"] == sku_id) & (master["location_id"] == location_id)]
        if md.empty:
            continue

        lead_time_days = int(md.iloc[0]["lead_time_days"])
        region = md.iloc[0]["region"]
        category = md.iloc[0]["category"]

        df_future = build_future_features(orders, sku_id, location_id, last_date)
        df_forecast = forecast_series(model, df_future)

        reorder_point, demand_next_lt, demand_horizon, stockout_risk, overstock_risk = compute_inventory_actions(
            df_forecast, on_hand, lead_time_days
        )

        results.append({
            "sku_id": sku_id,
            "location_id": location_id,
            "region": region,
            "category": category,
            "as_of_date": last_date.strftime("%Y-%m-%d"),
            "on_hand": on_hand,
            "lead_time_days": lead_time_days,
            "reorder_point": reorder_point,
            "forecast_demand_next_lead_time": demand_next_lt,
            "forecast_demand_horizon": demand_horizon,
            "stockout_risk": int(stockout_risk),
            "overstock_risk": int(overstock_risk)
        })

    df_results = pd.DataFrame(results).sort_values(["stockout_risk", "overstock_risk"], ascending=[False, False])
    df_results.to_csv(r"data/alerts.csv", index=False)

    print("alerts created:", len(df_results))

if __name__ == "__main__":
    main()
