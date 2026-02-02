DROP TABLE IF EXISTS orders_daily;
DROP TABLE IF EXISTS inventory_snapshot_daily;
DROP TABLE IF EXISTS master_data;

CREATE TABLE orders_daily (
  date TEXT NOT NULL,
  sku_id TEXT NOT NULL,
  location_id TEXT NOT NULL,
  qty_sold INTEGER NOT NULL CHECK (qty_sold >= 0),
  channel TEXT,
  PRIMARY KEY (date, sku_id, location_id)
);

CREATE TABLE inventory_snapshot_daily (
  date TEXT NOT NULL,
  sku_id TEXT NOT NULL,
  location_id TEXT NOT NULL,
  on_hand INTEGER NOT NULL CHECK (on_hand >= 0),
  on_order INTEGER NOT NULL DEFAULT 0 CHECK (on_order >= 0),
  PRIMARY KEY (date, sku_id, location_id)
);

CREATE TABLE master_data (
  sku_id TEXT NOT NULL,
  location_id TEXT NOT NULL,
  category TEXT NOT NULL,
  unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
  region TEXT NOT NULL,
  lead_time_days INTEGER NOT NULL CHECK (lead_time_days >= 0),
  PRIMARY KEY (sku_id, location_id)
);

CREATE INDEX idx_orders_sku_loc_date ON orders_daily (sku_id, location_id, date);
CREATE INDEX idx_inventory_sku_loc_date ON inventory_snapshot_daily (sku_id, location_id, date);
