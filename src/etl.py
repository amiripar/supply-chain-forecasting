import sqlite3
import pandas as pd

db_path = r"data/sc.db"

con = sqlite3.connect(db_path)

orders = pd.read_sql("select * from orders_daily", con)
inventory = pd.read_sql("select * from inventory_snapshot_daily", con)
master = pd.read_sql("select * from master_data", con)

con.close()

df = orders.merge(inventory, on=["date", "sku_id", "location_id"])
df = df.merge(master, on=["sku_id", "location_id"])

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values(["sku_id", "location_id", "date"]).reset_index(drop=True)

g = df.groupby(["sku_id", "location_id"])["qty_sold"]

df["lag_1"] = g.shift(1)
df["lag_7"] = g.shift(7)
df["lag_14"] = g.shift(14)

df["rolling_mean_7"] = g.transform(lambda s: s.rolling(7, min_periods=7).mean())
df["rolling_std_7"] = g.transform(lambda s: s.rolling(7, min_periods=7).std())

df["day_of_week"] = df["date"].dt.dayofweek
df["month"] = df["date"].dt.month

df = df.dropna().reset_index(drop=True)

output_path = r"data/feature_data.csv"
df.to_csv(output_path, index=False)

print("feature data created")
