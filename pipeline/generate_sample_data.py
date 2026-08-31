"""Create deterministic synthetic enterprise sales data for the portfolio demo."""

from pathlib import Path

import numpy as np
import pandas as pd

PRODUCTS = pd.DataFrame(
    [
        ("P-100", "Alpine Field Kit", "Field Equipment", 420.0, 248.0, "Northstar Manufacturing"),
        ("P-110", "Apex Sensor", "Electronics", 285.0, 171.0, "Helio Components"),
        ("P-120", "Transit Pro Case", "Accessories", 148.0, 82.0, "Northstar Manufacturing"),
        ("P-130", "Base Camp Hub", "Electronics", 620.0, 391.0, "Helio Components"),
        ("P-140", "Summit Battery", "Power", 215.0, 129.0, "Volta Supply"),
        ("P-150", "Trailhead Gateway", "Connectivity", 510.0, 306.0, "Volta Supply"),
    ],
    columns=["product_id", "product_name", "category", "list_price", "standard_cost", "supplier"],
)

REGIONS = ["Central", "East", "South", "West"]


def generate_sales(rows: int = 18_274, seed: int = 42) -> pd.DataFrame:
    """Return valid transactions plus known bad rows for quality-rule testing."""
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2025-01-01")
    end = pd.Timestamp("2026-08-31")
    day_span = (end - start).days
    product_index = rng.integers(0, len(PRODUCTS), rows)
    order_dates = start + pd.to_timedelta(rng.integers(0, day_span + 1, rows), unit="D")
    trend = 1 + ((order_dates - start).days.to_numpy() / day_span) * 0.22
    seasonal = np.where(order_dates.month.isin([10, 11, 12]), 1.18, 1.0)
    units = np.maximum(1, rng.poisson(6.2 * trend * seasonal)).astype(int)
    list_prices = PRODUCTS.iloc[product_index]["list_price"].to_numpy()
    standard_costs = PRODUCTS.iloc[product_index]["standard_cost"].to_numpy()
    discounts = np.round(rng.choice([0, 0.03, 0.05, 0.08, 0.12], rows, p=[0.32, 0.2, 0.25, 0.17, 0.06]), 2)

    data = pd.DataFrame(
        {
            "order_id": [f"VO-{value:06d}" for value in range(1, rows + 1)],
            "order_date": order_dates,
            "product_id": PRODUCTS.iloc[product_index]["product_id"].to_numpy(),
            "region": rng.choice(REGIONS, rows, p=[0.29, 0.25, 0.22, 0.24]),
            "units": units,
            "unit_price": np.round(list_prices * rng.normal(1.0, 0.025, rows), 2),
            "unit_cost": np.round(standard_costs * rng.normal(1.0, 0.02, rows), 2),
            "discount_pct": discounts,
            "freight_cost": np.round(rng.gamma(2.2, 5.0, rows), 2),
            "supplier_delay_days": np.maximum(0, rng.poisson(1.8, rows) + rng.choice([0, 4], rows, p=[0.94, 0.06])),
            "inventory_on_hand": rng.integers(80, 1100, rows),
        }
    )

    missing = data.sample(120, random_state=seed).copy()
    missing["order_id"] = [f"BAD-{value:04d}" for value in range(120)]
    missing["product_id"] = None
    duplicates = data.head(26).copy()
    return pd.concat([data, missing, duplicates], ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)


def write_sources(raw_dir: Path) -> tuple[Path, Path]:
    """Write the sales fact file and product reference file."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    sales_path = raw_dir / "sales.csv"
    products_path = raw_dir / "products.csv"
    generate_sales().to_csv(sales_path, index=False)
    PRODUCTS.to_csv(products_path, index=False)
    return sales_path, products_path
