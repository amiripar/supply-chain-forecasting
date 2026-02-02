import os
import pandas as pd
import streamlit as st
import sqlite3
import joblib
import numpy as np
from datetime import timedelta

db_path = r"data/sc.db"
model_path = r"data/forecast_model.pkl"
alerts_path = r"data/alerts.csv"
horizon_days = 14

def load_alerts():
    if not os.path.exists(alerts_path):
        return pd.DataFrame()
    return pd.read_csv(alerts_path)

def load_master():
    con = sqlite3.connect(db_path)
    master = pd.read_sql("select * from master_data", con)
    con.close()
    return master

def load_orders_for_pair(sku_id, location_id):
    con = sqlite3.connect(db_path)
    orders = pd.read_sql(
        "select date, sku_id, location_id, qty_sold from orders_daily where sku_id = ? and location_id = ?",
        con,
        params=(sku_id, location_id)
    )
    con.close()
    orders["date"] = pd.to_datetime(orders["date"])
    orders = orders.sort_values("date")
    return orders

def load_last_date():
    con = sqlite3.connect(db_path)
    d = pd.read_sql("select max(date) as last_date from orders_daily", con)
    con.close()
    return pd.to_datetime(d.loc[0, "last_date"])

def build_future_features(orders, last_date):
    s = orders.sort_values("date").set_index("date")[["qty_sold"]]
    future_dates = [last_date + timedelta(days=i) for i in range(1, horizon_days + 1)]
    history = s["qty_sold"].copy()

    rows = []
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

def forecast_series(df_future):
    model = joblib.load(model_path)
    features = ["lag_1", "lag_7", "lag_14", "rolling_mean_7", "rolling_std_7", "day_of_week", "month"]
    preds = model.predict(df_future[features])
    df_future["forecast_qty"] = np.maximum(0, np.round(preds)).astype(int)
    return df_future

st.set_page_config(page_title="inventory forecasting dashboard", layout="wide")
st.title("inventory forecasting dashboard")

alerts = load_alerts()
if alerts.empty:
    st.warning("alerts.csv not found. run: python src/forecast.py")
    st.stop()

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

total_rows = len(alerts)
stockout_count = int(alerts["stockout_risk"].sum())
overstock_count = int(alerts["overstock_risk"].sum())
avg_on_hand = float(alerts["on_hand"].mean())

kpi_col1.metric("rows", f"{total_rows}")
kpi_col2.metric("stockout risk", f"{stockout_count}")
kpi_col3.metric("overstock risk", f"{overstock_count}")
kpi_col4.metric("avg on hand", f"{avg_on_hand:.1f}")

st.divider()

left, right = st.columns([1, 2])

with left:
    regions = ["all"] + sorted(alerts["region"].dropna().unique().tolist())
    categories = ["all"] + sorted(alerts["category"].dropna().unique().tolist())

    region_filter = st.selectbox("region", regions)
    category_filter = st.selectbox("category", categories)

    stockout_only = st.checkbox("stockout only", value=False)
    overstock_only = st.checkbox("overstock only", value=False)

    filtered = alerts.copy()
    if region_filter != "all":
        filtered = filtered[filtered["region"] == region_filter]
    if category_filter != "all":
        filtered = filtered[filtered["category"] == category_filter]
    if stockout_only:
        filtered = filtered[filtered["stockout_risk"] == 1]
    if overstock_only:
        filtered = filtered[filtered["overstock_risk"] == 1]

    st.subheader("alerts")
    st.dataframe(filtered, use_container_width=True, height=420)

with right:
    st.subheader("sku drilldown")

    sku_list = sorted(alerts["sku_id"].unique().tolist())
    loc_list = sorted(alerts["location_id"].unique().tolist())

    sku_id = st.selectbox("sku_id", sku_list)
    location_id = st.selectbox("location_id", loc_list)

    row = alerts[(alerts["sku_id"] == sku_id) & (alerts["location_id"] == location_id)]
    if not row.empty:
        r = row.iloc[0]
        st.write({
            "as_of_date": r["as_of_date"],
            "on_hand": int(r["on_hand"]),
            "lead_time_days": int(r["lead_time_days"]),
            "reorder_point": int(r["reorder_point"]),
            "forecast_demand_next_lead_time": int(r["forecast_demand_next_lead_time"]),
            "stockout_risk": int(r["stockout_risk"]),
            "overstock_risk": int(r["overstock_risk"])
        })

    orders = load_orders_for_pair(sku_id, location_id)
    last_date = load_last_date()

    df_future = build_future_features(orders, last_date)
    df_forecast = forecast_series(df_future)

    last_60 = orders.tail(60).copy()
    last_60 = last_60.rename(columns={"qty_sold": "actual_qty"})

    df_plot = pd.concat(
        [
            last_60[["date", "actual_qty"]].assign(series="actual"),
            df_forecast[["date", "forecast_qty"]].rename(columns={"forecast_qty": "actual_qty"}).assign(series="forecast")
        ],
        ignore_index=True
    )

    st.line_chart(df_plot, x="date", y="actual_qty", color="series")

st.divider()
st.caption("data sources: data/sc.db and data/alerts.csv")
