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
