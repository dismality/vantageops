"""Validation, business metrics, forecasting, and explainable risk rules."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {
    "order_id", "order_date", "product_id", "region", "units", "unit_price",
    "unit_cost", "discount_pct", "freight_cost", "supplier_delay_days", "inventory_on_hand",
}


@dataclass(frozen=True)
class ValidationResult:
    clean: pd.DataFrame
    quarantined: pd.DataFrame
    checks: dict[str, float]


def validate_sales(sales: pd.DataFrame, products: pd.DataFrame) -> ValidationResult:
    """Separate trustworthy rows from duplicates, missing fields, and bad product keys."""
    missing_columns = REQUIRED_COLUMNS.difference(sales.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    valid_products = set(products["product_id"])
    duplicate_mask = sales.duplicated(subset=["order_id"], keep="first")
    missing_mask = sales[list(REQUIRED_COLUMNS)].isna().any(axis=1)
    invalid_product_mask = ~sales["product_id"].isin(valid_products) & sales["product_id"].notna()
    bad_mask = duplicate_mask | missing_mask | invalid_product_mask
    total = max(len(sales), 1)
    checks = {
        "required_fields_present": round((1 - missing_mask.mean()) * 100, 2),
        "valid_product_references": round((1 - invalid_product_mask.mean()) * 100, 2),
        "unique_order_ids": round((1 - duplicate_mask.mean()) * 100, 2),
        "accepted_rows": round((1 - bad_mask.mean()) * 100, 2),
    }
    return ValidationResult(sales.loc[~bad_mask].copy(), sales.loc[bad_mask].copy(), checks)


def enrich_sales(clean: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Apply finance definitions once so every dashboard view uses the same logic."""
    enriched = clean.merge(products, on="product_id", how="left", validate="many_to_one")
    enriched["order_date"] = pd.to_datetime(enriched["order_date"])
    enriched["gross_revenue"] = enriched["units"] * enriched["unit_price"]
    enriched["net_revenue"] = enriched["gross_revenue"] * (1 - enriched["discount_pct"])
    enriched["gross_profit"] = enriched["net_revenue"] - enriched["units"] * enriched["unit_cost"] - enriched["freight_cost"]
    enriched["margin_pct"] = np.where(enriched["net_revenue"] > 0, enriched["gross_profit"] / enriched["net_revenue"] * 100, 0)
    enriched["month"] = enriched["order_date"].dt.to_period("M").dt.to_timestamp()
    return enriched


def monthly_mart(enriched: pd.DataFrame) -> pd.DataFrame:
    """Create the executive monthly performance table."""
    monthly = enriched.groupby("month", as_index=False).agg(net_revenue=("net_revenue", "sum"), gross_profit=("gross_profit", "sum"), units=("units", "sum"), orders=("order_id", "nunique"))
    monthly["margin_pct"] = monthly["gross_profit"] / monthly["net_revenue"] * 100
    return monthly.sort_values("month")


def forecast_revenue(monthly: pd.DataFrame, periods: int = 3) -> pd.DataFrame:
    """Produce a simple, explainable trend forecast and 90% confidence range."""
    history = monthly.tail(12).reset_index(drop=True)
    x = np.arange(len(history), dtype=float)
    y = history["net_revenue"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    residual_std = float(np.std(y - (slope * x + intercept), ddof=1))
    future_x = np.arange(len(history), len(history) + periods, dtype=float)
    prediction = slope * future_x + intercept
    future_months = pd.date_range(history["month"].max() + pd.offsets.MonthBegin(1), periods=periods, freq="MS")
    return pd.DataFrame({"month": future_months, "forecast": prediction, "lower": prediction - 1.645 * residual_std, "upper": prediction + 1.645 * residual_std})


def calculate_kpis(enriched: pd.DataFrame) -> dict[str, float]:
    """Calculate the four headline measures used by executives."""
    revenue = float(enriched["net_revenue"].sum())
    profit = float(enriched["gross_profit"].sum())
    inventory_snapshots = enriched.sort_values("order_date").groupby(["month", "product_id"]).tail(1).copy()
    inventory_snapshots["inventory_value"] = inventory_snapshots["inventory_on_hand"] * inventory_snapshots["unit_cost"]
    average_inventory_value = float(inventory_snapshots.groupby("month")["inventory_value"].sum().mean())
    covered_days = max((enriched["order_date"].max() - enriched["order_date"].min()).days, 1)
    annualized_cost = float((enriched["units"] * enriched["unit_cost"]).sum()) * (365 / covered_days)
    return {
        "net_revenue": revenue,
        "gross_margin_pct": profit / revenue * 100,
        "inventory_turnover": annualized_cost / average_inventory_value,
        "accepted_rows": float(len(enriched)),
    }


def build_risk_alerts(enriched: pd.DataFrame) -> list[dict[str, object]]:
    """Rank operational signals using financial exposure and confidence."""
    product_region = enriched.groupby(["product_name", "region"], as_index=False).agg(revenue=("net_revenue", "sum"), units=("units", "sum"), stock=("inventory_on_hand", "last"), delay=("supplier_delay_days", "mean"), margin=("margin_pct", "mean"))
    product_region["stock_cover"] = product_region["stock"] / np.maximum(product_region["units"] / 86, 1)
    product_region["exposure"] = np.where(product_region["stock_cover"] < 3, product_region["revenue"] * 0.12, product_region["revenue"] * 0.035) + np.where(product_region["delay"] > 2.3, product_region["revenue"] * 0.04, 0)
    product_region["score"] = product_region["exposure"] * (1 + np.maximum(0, 3 - product_region["stock_cover"]) / 3)
    top = product_region.nlargest(5, "score")
    alerts: list[dict[str, object]] = []
    for rank, row in enumerate(top.itertuples(index=False), start=1):
        severity = "Critical" if rank == 1 else "High" if rank <= 3 else "Medium"
        alerts.append({"severity": severity, "product": row.product_name, "region": row.region, "exposure": round(float(row.exposure), 2), "confidence": max(76, 96 - rank * 3), "reason": "Low stock cover" if row.stock_cover < 3 else "Supplier delay"})
    return alerts
