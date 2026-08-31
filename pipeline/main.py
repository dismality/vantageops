"""Run the complete VantageOps pipeline from source files to analytics marts."""

import json
import sqlite3
from pathlib import Path

import pandas as pd

from pipeline.analytics import build_risk_alerts, calculate_kpis, enrich_sales, forecast_revenue, monthly_mart, validate_sales
from pipeline.generate_sample_data import write_sources

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def run_pipeline() -> dict[str, object]:
    """Execute ingestion, quality checks, transformations, forecast, and publishing."""
    sales_path, products_path = write_sources(RAW_DIR)
    sales = pd.read_csv(sales_path)
    products = pd.read_csv(products_path)
    validation = validate_sales(sales, products)
    enriched = enrich_sales(validation.clean, products)
    monthly = monthly_mart(enriched)
    forecast = forecast_revenue(monthly)
    kpis = calculate_kpis(enriched)
    alerts = build_risk_alerts(enriched)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    validation.quarantined.to_csv(PROCESSED_DIR / "quarantined_rows.csv", index=False)
    monthly.to_csv(PROCESSED_DIR / "monthly_performance.csv", index=False)
    forecast.to_csv(PROCESSED_DIR / "revenue_forecast.csv", index=False)
    with sqlite3.connect(PROCESSED_DIR / "vantageops.db") as connection:
        enriched.to_sql("fact_sales", connection, if_exists="replace", index=False)
        monthly.to_sql("mart_monthly_performance", connection, if_exists="replace", index=False)

    payload: dict[str, object] = {
        "generated_at": "2026-08-31T06:00:00Z",
        "source_rows": len(sales),
        "accepted_rows": len(validation.clean),
        "quarantined_rows": len(validation.quarantined),
        "quality_checks": validation.checks,
        "kpis": {key: round(value, 2) for key, value in kpis.items()},
        "forecast": json.loads(forecast.assign(month=forecast["month"].astype(str)).to_json(orient="records")),
        "risk_alerts": alerts,
    }
    (PROCESSED_DIR / "dashboard_data.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = run_pipeline()
    print(f"Pipeline complete: {result['accepted_rows']:,} accepted, {result['quarantined_rows']:,} quarantined")
