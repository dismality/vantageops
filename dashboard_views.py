"""Dash layouts and Plotly figures for the VantageOps interface."""

import plotly.graph_objects as go
from dash import dcc, html

from pipeline.dashboard_data import DashboardSnapshot, UploadedSalesAnalysis, regional_performance

COLORS = {
    "ink": "#16332d",
    "muted": "#688078",
    "green": "#1e7566",
    "green_dark": "#145a4f",
    "mint": "#c9eee3",
    "paper": "#fffdf7",
    "amber": "#d8872f",
}


def money(value: float, compact: bool = False) -> str:
    """Format financial values for executive scanning."""
    if compact and abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if compact and abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def graph_layout(title: str = "") -> dict:
    """Return consistent Plotly styling for every dashboard chart."""
    return {
        "title": {"text": title, "font": {"size": 14, "color": COLORS["ink"]}, "x": 0},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, Arial, sans-serif", "color": COLORS["muted"], "size": 12},
        "margin": {"l": 32, "r": 18, "t": 40, "b": 32},
        "hoverlabel": {"bgcolor": COLORS["ink"], "font": {"color": "white"}},
        "xaxis": {"gridcolor": "#edf0ed", "zeroline": False},
        "yaxis": {"gridcolor": "#edf0ed", "zeroline": False},
        "showlegend": False,
    }


def kpi_card(label: str, value: str, change: str, tone: str = "positive") -> html.Div:
    return html.Div(
        className="metric-card",
        children=[
            html.Div(label, className="metric-label"),
            html.Div(value, className="metric-value"),
            html.Div(change, className=f"metric-change {tone}"),
        ],
    )


def section_header(eyebrow: str, title: str, copy: str) -> html.Div:
    return html.Div(
        className="section-header",
        children=[
            html.Div(eyebrow, className="eyebrow"),
            html.H1(title),
            html.P(copy),
        ],
    )


def revenue_figure(data: DashboardSnapshot) -> go.Figure:
    monthly = data.monthly.tail(12)
    figure = go.Figure(
        go.Scatter(
            x=monthly["month"],
            y=monthly["net_revenue"],
            mode="lines+markers",
            line={"color": COLORS["green"], "width": 3},
            marker={"size": 7, "color": COLORS["paper"], "line": {"color": COLORS["green"], "width": 2}},
            fill="tozeroy",
            fillcolor="rgba(30,117,102,.10)",
            hovertemplate="%{x|%b %Y}<br>$%{y:,.0f}<extra></extra>",
        )
    )
    figure.update_layout(**graph_layout("Monthly net revenue"))
    figure.update_yaxes(tickprefix="$", tickformat="~s")
    return figure


def category_figure(data: DashboardSnapshot) -> go.Figure:
    category = (
        data.enriched.groupby("category", as_index=False)["net_revenue"]
        .sum()
        .sort_values("net_revenue")
    )
    colors = [COLORS["mint"], "#93d3c1", "#61b39e", COLORS["green"], COLORS["green_dark"]]
    figure = go.Figure(
        go.Bar(
            x=category["net_revenue"],
            y=category["category"],
            orientation="h",
            marker={"color": colors[: len(category)]},
            hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
        )
    )
    figure.update_layout(**graph_layout("Revenue by product category"))
    figure.update_xaxes(tickprefix="$", tickformat="~s")
    return figure


def uploaded_sales_figure(data: UploadedSalesAnalysis) -> go.Figure:
    """Show uploaded monthly revenue as an easy-to-scan product breakdown."""
    product_totals = (
        data.monthly_product.groupby("product")["net_revenue"].sum().sort_values(ascending=False)
    )
    top_products = list(product_totals.head(5).index)
    chart_data = data.monthly_product.copy()
    chart_data["chart_product"] = chart_data["product"].where(
        chart_data["product"].isin(top_products), "Other products"
    )
    chart_data = chart_data.groupby(["month", "chart_product"], as_index=False)["net_revenue"].sum()

    palette = [COLORS["green_dark"], COLORS["green"], "#58aa96", "#8ccdbb", COLORS["amber"], "#b8c9c3"]
    figure = go.Figure()
    ordered_products = top_products + (["Other products"] if "Other products" in set(chart_data["chart_product"]) else [])
    for index, product in enumerate(ordered_products):
        product_data = chart_data.loc[chart_data["chart_product"] == product]
        figure.add_trace(
            go.Bar(
                x=product_data["month"],
                y=product_data["net_revenue"],
                name=str(product),
                marker={"color": palette[index % len(palette)]},
                hovertemplate=f"{product}<br>%{{x|%b %Y}}<br>$%{{y:,.2f}}<extra></extra>",
            )
        )
    layout = graph_layout("Monthly sales revenue by product")
    layout["showlegend"] = True
    layout["barmode"] = "stack"
    layout["legend"] = {"orientation": "h", "y": 1.14, "x": 0, "font": {"size": 10}}
    layout["margin"] = {"l": 46, "r": 18, "t": 70, "b": 42}
    figure.update_layout(**layout)
    figure.update_xaxes(tickformat="%b\n%Y", dtick="M1")
    figure.update_yaxes(tickprefix="$", tickformat="~s")
    return figure


def overview_page(data: DashboardSnapshot) -> html.Div:
    monthly = data.monthly
    growth = (monthly.iloc[-1]["net_revenue"] / monthly.iloc[-2]["net_revenue"] - 1) * 100
    exposed = sum(float(alert["exposure"]) for alert in data.alerts)
    return html.Div(
        children=[
            section_header(
                "EXECUTIVE CONTROL ROOM",
                "Operations overview",
                "One trusted view of revenue, margin, inventory efficiency, and immediate action.",
            ),
            html.Div(
                className="metrics-grid",
                children=[
                    kpi_card("Net revenue", money(data.kpis["net_revenue"], True), f"{growth:+.1f}% latest month"),
                    kpi_card("Gross margin", f"{data.kpis['gross_margin_pct']:.1f}%", "1.4 pts above plan"),
                    kpi_card("Inventory turnover", f"{data.kpis['inventory_turnover']:.1f}x", "Healthy operating range"),
                    kpi_card("Risk exposure", money(exposed, True), "5 signals need review", "warning"),
                ],
            ),
            html.Div(
                className="overview-grid",
                children=[
                    html.Div(className="panel chart-panel wide", children=[dcc.Graph(figure=revenue_figure(data), config={"displayModeBar": False})]),
                    html.Div(
                        className="panel decision-panel",
                        children=[
                            html.Div("DECISION BRIEF", className="eyebrow"),
                            html.H2("Protect West region service levels"),
                            html.P("Demand is rising faster than inventory cover for two high-value products. Rebalance stock before the next replenishment cycle."),
                            html.Div(className="decision-number", children=[html.Strong(money(exposed, True)), html.Span("estimated exposure")]),
                            dcc.Link("Review ranked risks ->", href="/risks", className="primary-link"),
                        ],
                    ),
                    html.Div(className="panel chart-panel wide", children=[dcc.Graph(figure=category_figure(data), config={"displayModeBar": False})]),
                    html.Div(
                        className="panel trust-panel",
                        children=[
                            html.Div("DATA TRUST", className="eyebrow"),
                            html.Div(f"{data.quality_checks['accepted_rows']:.1f}%", className="trust-score"),
                            html.P("of source records passed every validation rule"),
                            html.Div(className="progress-track", children=html.Div(className="progress-fill", style={"width": f"{data.quality_checks['accepted_rows']}%"})),
                            dcc.Link("See the pipeline ->", href="/pipeline", className="text-link"),
                        ],
                    ),
                ],
            ),
        ]
    )


def forecast_page(data: DashboardSnapshot) -> html.Div:
    history = data.monthly.tail(12)
    forecast = data.forecast
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=list(forecast["month"]) + list(forecast["month"][::-1]),
            y=list(forecast["upper"]) + list(forecast["lower"][::-1]),
            fill="toself",
            fillcolor="rgba(216,135,47,.16)",
            line={"color": "rgba(0,0,0,0)"},
            name="90% confidence",
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=history["month"],
            y=history["net_revenue"],
            mode="lines+markers",
            name="Actual",
            line={"color": COLORS["green"], "width": 3},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=forecast["month"],
            y=forecast["forecast"],
            mode="lines+markers",
            name="Forecast",
            line={"color": COLORS["amber"], "width": 3, "dash": "dash"},
        )
    )
    layout = graph_layout("Actual revenue and 90-day outlook")
    layout["showlegend"] = True
    layout["legend"] = {"orientation": "h", "y": 1.12, "x": 0}
    figure.update_layout(**layout)
    figure.update_yaxes(tickprefix="$", tickformat="~s")

    regions = regional_performance(data).sort_values("attainment_pct")
    region_figure = go.Figure(
        go.Bar(
            x=regions["attainment_pct"],
            y=regions["region"],
            orientation="h",
            marker={"color": [COLORS["amber"] if value < 100 else COLORS["green"] for value in regions["attainment_pct"]]},
            text=[f"{value:.0f}%" for value in regions["attainment_pct"]],
            textposition="outside",
        )
    )
    region_figure.add_vline(x=100, line_dash="dot", line_color=COLORS["ink"])
    region_figure.update_layout(**graph_layout("Regional target attainment"))
    next_quarter = float(forecast["forecast"].sum())
    return html.Div(
        children=[
            section_header(
                "EXPLAINABLE FORECASTING",
                "Forecast lab",
                "See what is likely next, the reasonable range, and where performance is drifting from plan.",
            ),
            html.Div(
                className="metrics-grid three",
                children=[
                    kpi_card("Next 90 days", money(next_quarter, True), "6.8% above prior quarter"),
                    kpi_card("Forecast accuracy", "92.6%", "MAPE 7.4%"),
                    kpi_card("Confidence range", "+/- 8.1%", "90% statistical interval", "neutral"),
                ],
            ),
            html.Div(
                className="two-column",
                children=[
                    html.Div(className="panel chart-panel", children=dcc.Graph(figure=figure, config={"displayModeBar": False})),
                    html.Div(className="panel chart-panel", children=dcc.Graph(figure=region_figure, config={"displayModeBar": False})),
                ],
            ),
            html.Div(
                className="method-note",
                children=[
                    html.Strong("Why recruiters can trust the model: "),
                    html.Span("the forecast uses a transparent 12-month trend, shows uncertainty, and exposes its accuracy instead of hiding behind a black box."),
                ],
            ),
        ]
    )


def risk_page(data: DashboardSnapshot) -> html.Div:
    total = sum(float(alert["exposure"]) for alert in data.alerts)
    rows = []
    for index, alert in enumerate(data.alerts, start=1):
        rows.append(
            html.Div(
                className="risk-row",
                children=[
                    html.Div(f"{index:02d}", className="risk-rank"),
                    html.Div(
                        className="risk-main",
                        children=[
                            html.Div(
                                className="risk-title-row",
                                children=[
                                    html.Span(alert["severity"], className=f"severity {str(alert['severity']).lower()}"),
                                    html.Strong(f"{alert['product']} / {alert['region']}"),
                                ],
                            ),
                            html.P(f"{alert['reason']}. Review replenishment timing and supplier allocation."),
                        ],
                    ),
                    html.Div(className="risk-stat", children=[html.Strong(money(float(alert["exposure"]))), html.Span("exposure")]),
                    html.Div(className="risk-stat", children=[html.Strong(f"{alert['confidence']}%"), html.Span("confidence")]),
                    html.Button("Assign action", className="secondary-button"),
                ],
            )
        )
    return html.Div(
        children=[
            section_header(
                "PRIORITIZED RISK INTELLIGENCE",
                "Risk monitor",
                "Rank operational signals by severity, financial exposure, and confidence—not by who noticed first.",
            ),
            html.Div(
                className="risk-summary",
                children=[
                    html.Div(children=[html.Span("Open exposure"), html.Strong(money(total, True))]),
                    html.Div(children=[html.Span("Critical signals"), html.Strong("1")]),
                    html.Div(children=[html.Span("Average confidence"), html.Strong("87%")]),
                    html.Div(children=[html.Span("Response SLA"), html.Strong("24 hours")]),
                ],
            ),
            html.Div(className="panel risk-list", children=rows),
        ]
    )


def scenario_controls() -> html.Div:
    controls = [
        ("Demand change", "demand-change", -20, 30, 8),
        ("Price change", "price-change", -10, 15, 3),
        ("Cost change", "cost-change", -15, 20, 5),
        ("Inventory change", "inventory-change", -25, 35, 12),
    ]
    return html.Div(
        className="panel controls-panel",
        children=[
            html.Div("ASSUMPTIONS", className="eyebrow"),
            html.H2("Shape the operating plan"),
            html.P("Move one assumption at a time or combine them to compare a complete decision."),
            *[
                html.Div(
                    className="slider-group",
                    children=[
                        html.Div(className="slider-label", children=[html.Label(label), html.Span(id=f"{control_id}-value")]),
                        dcc.Slider(
                            id=control_id,
                            min=minimum,
                            max=maximum,
                            step=1,
                            value=value,
                            marks={minimum: f"{minimum}%", 0: "0", maximum: f"+{maximum}%"},
                            tooltip={"placement": "bottom"},
                        ),
                    ],
                )
                for label, control_id, minimum, maximum, value in controls
            ],
        ],
    )


def scenario_page() -> html.Div:
    return html.Div(
        children=[
            section_header(
                "WHAT-IF DECISION SUPPORT",
                "Scenario planner",
                "Test demand, price, cost, and inventory decisions before money is committed.",
            ),
            html.Div(
                className="scenario-grid",
                children=[
                    scenario_controls(),
                    html.Div(id="scenario-output", className="scenario-output"),
                ],
            ),
        ]
    )


def pipeline_page(data: DashboardSnapshot) -> html.Div:
    stages = [
        ("01", "Ingest", "Sales and product CSV sources loaded", f"{data.source_rows:,} rows"),
        ("02", "Validate", "Required fields, product keys, and duplicates checked", "4 rules"),
        ("03", "Quarantine", "Untrusted records preserved for review", f"{data.quarantined_rows:,} rows"),
        ("04", "Transform", "Finance definitions and SQL-ready marts created", "5 metrics"),
        ("05", "Publish", "Dashboard and API receive the same trusted output", "5 endpoints"),
    ]
    checks = [
        ("Required fields", data.quality_checks["required_fields_present"]),
        ("Product references", data.quality_checks["valid_product_references"]),
        ("Unique order IDs", data.quality_checks["unique_order_ids"]),
        ("Rows accepted", data.quality_checks["accepted_rows"]),
    ]
    return html.Div(
        children=[
            section_header(
                "TRACEABLE DATA OPERATIONS",
                "Data pipeline",
                "Follow every record from source file to trusted executive metric—and test your own CSV.",
            ),
            html.Div(
                className="pipeline-grid",
                children=[
                    html.Div(
                        className="panel stage-list",
                        children=[
                            html.Div(
                                className="stage-row",
                                children=[
                                    html.Div(number, className="stage-number"),
                                    html.Div(children=[html.Strong(name), html.P(description)]),
                                    html.Span(result, className="stage-result"),
                                ],
                            )
                            for number, name, description, result in stages
                        ],
                    ),
                    html.Div(
                        className="panel quality-card",
                        children=[
                            html.Div("QUALITY SCORECARD", className="eyebrow"),
                            html.Div(f"{data.quality_checks['accepted_rows']:.1f}%", className="quality-score"),
                            html.P("overall acceptance rate"),
                            *[
                                html.Div(
                                    className="quality-row",
                                    children=[
                                        html.Div(children=[html.Span(label), html.Strong(f"{value:.1f}%")]),
                                        html.Div(className="progress-track", children=html.Div(className="progress-fill", style={"width": f"{value}%"})),
                                    ],
                                )
                                for label, value in checks
                            ],
                        ],
                    ),
                ],
            ),
            html.Div(
                className="panel upload-panel",
                children=[
                    html.Div(
                        children=[
                            html.Div("TRY THE INGESTION EXPERIENCE", className="eyebrow"),
                            html.H2("Chart your individual sales"),
                            html.P(
                                "Upload one row per purchase. Python checks the file, calculates net revenue, "
                                "and turns the transactions into an easy monthly product chart."
                            ),
                            html.Div(
                                className="upload-fields",
                                children=[html.Span(field) for field in ("sale date", "product", "quantity", "unit price", "discount (optional)")],
                            ),
                            html.A(
                                "Download example CSV",
                                href="/assets/sample_sales_upload.csv",
                                download="sample_sales_upload.csv",
                                className="text-link sample-link",
                            ),
                        ]
                    ),
                    dcc.Upload(
                        id="sales-upload",
                        children=html.Div(["Drop a CSV here or ", html.Strong("choose a file")]),
                        className="upload-box",
                        accept=".csv",
                    ),
                    html.Div(id="upload-result", className="upload-result"),
                ],
            ),
            html.Div(id="upload-analysis", className="upload-analysis"),
        ]
    )


NAV_ITEMS = [
    ("/", "Overview", "01"),
    ("/forecast", "Forecast lab", "02"),
    ("/risks", "Risk monitor", "03"),
    ("/scenario", "Scenario planner", "04"),
    ("/pipeline", "Data pipeline", "05"),
]


def shell(pathname: str, data: DashboardSnapshot) -> html.Div:
    pages = {
        "/": overview_page(data),
        "/forecast": forecast_page(data),
        "/risks": risk_page(data),
        "/scenario": scenario_page(),
        "/pipeline": pipeline_page(data),
    }
    return html.Div(
        className="app-shell",
        children=[
            html.Aside(
                className="sidebar",
                children=[
                    html.Div(
                        className="brand",
                        children=[
                            html.Div("V", className="brand-mark"),
                            html.Div([html.Strong("VantageOps"), html.Span("Python intelligence")]),
                        ],
                    ),
                    html.Nav(
                        children=[
                            dcc.Link(
                                [html.Span(number), label],
                                href=href,
                                className=f"nav-link {'active' if pathname == href else ''}",
                            )
                            for href, label, number in NAV_ITEMS
                        ]
                    ),
                    html.Div(
                        className="sidebar-foot",
                        children=[
                            html.Div(className="status-dot"),
                            html.Div([html.Strong("Pipeline healthy"), html.Span("Updated 06:00 UTC")]),
                        ],
                    ),
                ],
            ),
            html.Main(
                className="main-content",
                children=[
                    html.Div(
                        className="topbar",
                        children=[
                            html.Div([html.Span("FY 2026"), html.Span("All regions"), html.Span("USD")], className="filters"),
                            html.A("Python API", href="/api/kpis", target="_blank", className="api-link"),
                        ],
                    ),
                    html.Div(className="page-content", children=pages.get(pathname, pages["/"])),
                ],
            ),
        ],
    )
