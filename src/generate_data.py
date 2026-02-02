import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

db_path = r"data/sc.db"

start_date = datetime(2024, 1, 1)
days = 365

sku_list = [f"sku_{i}" for i in range(1, 21)]
location_list = ["loc_1", "loc_2", "loc_3"]
categories = ["electronics", "food", "clothing"]
regions = ["north", "south", "west"]

dates = [start_date + timedelta(days=i) for i in range(days)]

orders_data = []
inventory_data = []
master_data = []

for sku in sku_list:
    for loc in location_list:
        category = random.choice(categories)
        region = random.choice(regions)
        unit_cost = round(random.uniform(5, 200), 2)
        lead_time_days = random.randint(3, 14)
        master_data.append((sku, loc, category, unit_cost, region, lead_time_days))

        base_demand = random.randint(20, 100)
        seasonality = np.sin(np.linspace(0, 3 * np.pi, days)) * random.randint(5, 20)
        noise = np.random.normal(0, 5, days)

        demand_series = np.maximum(0, base_demand + seasonality + noise).astype(int)

        on_hand = random.randint(200, 500)

        for i, d in enumerate(dates):
            qty_sold = int(demand_series[i])
            orders_data.append((d.strftime("%Y-%m-%d"), sku, loc, qty_sold, "online"))

            on_hand = max(0, on_hand - qty_sold)
            on_order = 0

            if on_hand < 100:
                on_order = random.randint(100, 300)
                on_hand += on_order

            inventory_data.append((d.strftime("%Y-%m-%d"), sku, loc, on_hand, on_order))

con = sqlite3.connect(db_path)
cur = con.cursor()

cur.executemany(
    "INSERT INTO master_data (sku_id, location_id, category, unit_cost, region, lead_time_days) VALUES (?, ?, ?, ?, ?, ?)",
    master_data
)

cur.executemany(
    "INSERT INTO orders_daily (date, sku_id, location_id, qty_sold, channel) VALUES (?, ?, ?, ?, ?)",
    orders_data
)

cur.executemany(
    "INSERT INTO inventory_snapshot_daily (date, sku_id, location_id, on_hand, on_order) VALUES (?, ?, ?, ?, ?)",
    inventory_data
)

con.commit()
con.close()

print("data generated")
