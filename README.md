# Supply Chain Demand Forecasting & Inventory Decision Support System

## Project Overview
This project is an end-to-end supply chain forecasting system that predicts product demand and converts forecasts into operational inventory decisions such as reorder points and stockout/overstock alerts.

The system simulates a real logistics environment with multiple SKUs and locations and provides a dashboard for business users to monitor risks and trends.

## Business Problem
Logistics companies must balance:
- Avoiding stockouts (lost sales)
- Avoiding overstock (excess inventory cost)
- Making data-driven replenishment decisions

This project addresses these challenges by:
- Forecasting demand per SKU and location
- Calculating reorder points based on lead time and service level
- Highlighting risk scenarios in a dashboard

## Architecture
Data Flow:
SQL Database (SQLite)  
→ ETL & Feature Engineering  
→ Machine Learning Forecast Model (LightGBM)  
→ Inventory Decision Logic  
→ Streamlit Dashboard

## Data
Synthetic but realistic data is generated including:
- Daily sales (orders_daily)
- Daily inventory snapshots (inventory_snapshot_daily)
- Master data (lead time, region, category, unit cost)

Tables:
- orders_daily
- inventory_snapshot_daily
- master_data

## Feature Engineering
- Lag features: lag_1, lag_7, lag_14
- Rolling statistics: rolling_mean_7, rolling_std_7
- Calendar features: day_of_week, month

## Modeling
Baseline: Naive forecast (lag_1)  
Model: LightGBM Regressor  

Metrics:
- Baseline MAE ≈ 5.4  
- Model MAE ≈ 3.7  

## Inventory Decision Logic
Reorder Point:
mean demand during lead time + safety stock

Stockout Risk:
on_hand < forecast demand during lead time

Overstock Risk:
on_hand > 1.5 × forecast horizon demand

## Dashboard (Streamlit)
Features:
- KPI overview (stockout risk, overstock risk, average inventory)
- Filterable alerts table by region and category
- SKU drill-down view
- Actual vs forecast demand visualization

## How to Run

Create virtual environment:
python -m venv venv  
venv\Scripts\activate  

Install requirements:
pip install -r requirements.txt  

Create database schema:
python -c "import sqlite3; con=sqlite3.connect('data/sc.db'); con.executescript(open('sql/schema.sql').read()); con.commit(); con.close()"

Generate data:
python src/generate_data.py  

Build features:
python src/etl.py  

Train model:
python src/train.py  

Generate alerts:
python src/forecast.py  

Run dashboard:
streamlit run src/app.py  

## Technologies
- Python
- SQLite
- Pandas, NumPy
- LightGBM
- Scikit-learn
- Streamlit

## Business Value
This system demonstrates how machine learning can be operationalized in supply chain environments to:
- Improve forecasting accuracy
- Support inventory planning decisions
- Provide actionable insights through dashboards

## Use Case
Designed as a portfolio project aligned with supply chain analytics and data science roles in logistics companies such as DHL Supply Chain.
