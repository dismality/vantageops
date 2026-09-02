"""Prepare reusable dashboard data and business scenarios for the web app."""

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from pipeline.analytics import (
    build_risk_alerts,
    calculate_kpis,
    enrich_sales,
    forecast_revenue,
    monthly_mart,
    validate_sales,
)
from pipeline.generate_sample_data import PRODUCTS, generate_sales


@dataclass(frozen=True)
class DashboardSnapshot:
    """All trusted data used by the dashboard and its API."""

    enriched: pd.DataFrame
    monthly: pd.DataFrame
    forecast: pd.DataFrame
    kpis: dict[str, float]
    alerts: list[dict[str, object]]
    quality_checks: dict[str, float]
    source_rows: int
    accepted_rows: int
    quarantined_rows: int


@dataclass(frozen=True)
class UploadedSalesAnalysis:
    """Clean transactions and chart-ready summaries from an uploaded CSV."""

    clean: pd.DataFrame
    monthly: pd.DataFrame
    monthly_product: pd.DataFrame
    rejected_rows: int


@lru_cache(maxsize=1)
def load_snapshot() -> DashboardSnapshot:
    """Build the deterministic demo dataset once per application process."""
    sales = generate_sales()
    validation = validate_sales(sales, PRODUCTS)
    enriched = enrich_sales(validation.clean, PRODUCTS)
    monthly = monthly_mart(enriched)
    return DashboardSnapshot(
        enriched=enriched,
        monthly=monthly,
        forecast=forecast_revenue(monthly),
        kpis=calculate_kpis(enriched),
        alerts=build_risk_alerts(enriched),
        quality_checks=validation.checks,
        source_rows=len(sales),
        accepted_rows=len(validation.clean),
        quarantined_rows=len(validation.quarantined),
    )


def calculate_scenario(
    snapshot: DashboardSnapshot,
    demand_change: float,
    price_change: float,
    cost_change: float,
    inventory_change: float,
) -> dict[str, float]:
    """Estimate executive outcomes from four easy-to-explain assumptions."""
    demand_factor = 1 + demand_change / 100
    price_factor = 1 + price_change / 100
    cost_factor = 1 + cost_change / 100
    inventory_factor = 1 + inventory_change / 100
    base_revenue = snapshot.kpis["net_revenue"]
    base_margin = snapshot.kpis["gross_margin_pct"] / 100
    base_cost = base_revenue * (1 - base_margin)
    revenue = base_revenue * demand_factor * price_factor
    cost = base_cost * demand_factor * cost_factor
    gross_profit = revenue - cost
    margin = gross_profit / revenue * 100 if revenue else 0
    working_capital = 4_260_000 * inventory_factor
    service_level = min(99.5, max(82.0, 94.2 + inventory_change * 0.16 - demand_change * 0.08))
    return {
        "revenue": revenue,
        "gross_margin_pct": margin,
        "working_capital": working_capital,
        "service_level_pct": service_level,
        "profit_delta": gross_profit - (base_revenue - base_cost),
    }


def regional_performance(snapshot: DashboardSnapshot) -> pd.DataFrame:
    """Summarize regional results with an explicit revenue target."""
    grouped = (
        snapshot.enriched.groupby("region", as_index=False)
        .agg(revenue=("net_revenue", "sum"), gross_profit=("gross_profit", "sum"))
        .sort_values("revenue", ascending=False)
    )
    grouped["target"] = grouped["revenue"].mean() * 1.03
    grouped["attainment_pct"] = grouped["revenue"] / grouped["target"] * 100
    return grouped


def analyze_uploaded_sales(frame: pd.DataFrame) -> UploadedSalesAnalysis:
    """Turn a simple transaction-level sales file into monthly summaries.

    Friendly aliases let a business user upload common column names without
    first reshaping the file to match the larger demonstration data model.
    """
    if frame.empty:
        raise ValueError("The CSV does not contain any sales rows.")

    normalized = frame.copy()
    normalized.columns = [
        str(column).strip().lower().replace(" ", "_").replace("-", "_")
        for column in normalized.columns
    ]
    aliases = {
        "sale_date": ("sale_date", "order_date", "date", "transaction_date", "sold_at"),
        "product": ("product", "product_name", "item", "item_name", "product_id"),
        "quantity": ("quantity", "qty", "units", "units_sold"),
        "unit_price": ("unit_price", "price", "sale_price", "price_each"),
        "discount_pct": ("discount_pct", "discount", "discount_percent"),
    }

    selected: dict[str, str] = {}
    for target, choices in aliases.items():
        match = next((choice for choice in choices if choice in normalized.columns), None)
        if match:
            selected[target] = match

    required = ("sale_date", "product", "quantity", "unit_price")
    missing = [column for column in required if column not in selected]
    if missing:
        readable = ", ".join(missing)
        raise ValueError(
            f"Missing sales fields: {readable}. Use sale_date, product, quantity, and unit_price."
        )

    clean = pd.DataFrame(
        {
            target: normalized[source]
            for target, source in selected.items()
        }
    )
    if "discount_pct" not in clean:
        clean["discount_pct"] = 0.0

    clean["sale_date"] = pd.to_datetime(clean["sale_date"], errors="coerce")
    clean["product"] = clean["product"].astype("string").str.strip()
    for column in ("quantity", "unit_price", "discount_pct"):
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    clean["discount_pct"] = clean["discount_pct"].astype(float)

    # Accept either decimals (0.10) or familiar whole percentages (10).
    percent_mask = clean["discount_pct"].abs() > 1
    clean.loc[percent_mask, "discount_pct"] = clean.loc[percent_mask, "discount_pct"] / 100
    valid = (
        clean["sale_date"].notna()
        & clean["product"].notna()
        & clean["product"].ne("")
        & clean["quantity"].gt(0)
        & clean["unit_price"].ge(0)
        & clean["discount_pct"].between(0, 1, inclusive="both")
    )
    rejected_rows = int((~valid).sum())
    clean = clean.loc[valid].copy()
    if clean.empty:
        raise ValueError("No usable sales rows remained after checking dates, quantities, and prices.")

    clean["net_revenue"] = (
        clean["quantity"] * clean["unit_price"] * (1 - clean["discount_pct"])
    )
    clean["month"] = clean["sale_date"].dt.to_period("M").dt.to_timestamp()
    clean = clean.sort_values("sale_date").reset_index(drop=True)
    monthly = (
        clean.groupby("month", as_index=False)
        .agg(
            net_revenue=("net_revenue", "sum"),
            units=("quantity", "sum"),
            transactions=("product", "size"),
        )
        .sort_values("month")
    )
    monthly_product = (
        clean.groupby(["month", "product"], as_index=False)
        .agg(net_revenue=("net_revenue", "sum"), units=("quantity", "sum"))
        .sort_values(["month", "net_revenue"], ascending=[True, False])
    )
    return UploadedSalesAnalysis(clean, monthly, monthly_product, rejected_rows)
