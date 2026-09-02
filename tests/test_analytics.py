import pandas as pd

from pipeline.analytics import calculate_kpis, enrich_sales, forecast_revenue, monthly_mart, validate_sales
from pipeline.dashboard_data import analyze_uploaded_sales, calculate_scenario, load_snapshot
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


def test_uploaded_transactions_become_monthly_product_sales():
    frame = pd.DataFrame(
        {
            "Sale Date": ["2026-01-04", "2026-01-18", "2026-02-03", "not-a-date"],
            "Item": ["Analytics Pro", "Workflow Hub", "Analytics Pro", "Support AI"],
            "Qty": [2, 1, 3, 4],
            "Price": [10, 20, 10, 5],
            "Discount": [10, 0, 0.05, 0],
        }
    )
    result = analyze_uploaded_sales(frame)
    assert len(result.clean) == 3
    assert result.rejected_rows == 1
    assert len(result.monthly) == 2
    assert result.monthly.iloc[0]["net_revenue"] == 38
    assert result.monthly.iloc[1]["net_revenue"] == 28.5
    assert set(result.monthly_product["product"]) == {"Analytics Pro", "Workflow Hub"}


def test_uploaded_transactions_require_clear_sales_fields():
    try:
        analyze_uploaded_sales(pd.DataFrame({"date": ["2026-01-01"], "product": ["A"]}))
    except ValueError as error:
        assert "quantity" in str(error)
        assert "unit_price" in str(error)
    else:
        raise AssertionError("Expected an incomplete sales upload to be rejected")
