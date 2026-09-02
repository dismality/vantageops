import pandas as pd

from pipeline.analytics import calculate_kpis, enrich_sales, forecast_revenue, monthly_mart, validate_sales
from pipeline.dashboard_data import calculate_scenario, load_snapshot
from pipeline.generate_sample_data import PRODUCTS, generate_sales


def test_quality_rules_quarantine_known_bad_rows():
    result = validate_sales(generate_sales(), PRODUCTS)
    assert len(result.clean) == 18_274
    assert len(result.quarantined) == 146
    assert result.clean["order_id"].is_unique


def test_finance_metrics_are_positive_and_bounded():
    result = validate_sales(generate_sales(), PRODUCTS)
    enriched = enrich_sales(result.clean, PRODUCTS)
    kpis = calculate_kpis(enriched)
    assert kpis["net_revenue"] > 0
    assert 0 < kpis["gross_margin_pct"] < 100
    assert kpis["inventory_turnover"] > 0


def test_forecast_returns_three_ordered_months():
    result = validate_sales(generate_sales(), PRODUCTS)
    monthly = monthly_mart(enrich_sales(result.clean, PRODUCTS))
    forecast = forecast_revenue(monthly)
    assert len(forecast) == 3
    assert forecast["month"].is_monotonic_increasing
    assert (forecast["lower"] < forecast["forecast"]).all()
    assert (forecast["forecast"] < forecast["upper"]).all()


def test_missing_schema_is_rejected():
    try:
        validate_sales(pd.DataFrame({"order_id": ["1"]}), PRODUCTS)
    except ValueError as error:
        assert "Missing required columns" in str(error)
    else:
        raise AssertionError("Expected validation to reject an incomplete schema")


def test_scenario_reacts_to_business_assumptions():
    snapshot = load_snapshot()
    baseline = calculate_scenario(snapshot, 0, 0, 0, 0)
    growth = calculate_scenario(snapshot, 10, 4, 0, 8)
    assert growth["revenue"] > baseline["revenue"]
    assert growth["working_capital"] > baseline["working_capital"]
    assert 82 <= growth["service_level_pct"] <= 99.5
