"""VantageOps: a Python-first enterprise analytics dashboard and API."""

import base64
import io

import pandas as pd
from dash import Dash, Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate

from api import register_api
from dashboard_views import kpi_card, money, shell, uploaded_sales_figure
from pipeline.dashboard_data import analyze_uploaded_sales, calculate_scenario, load_snapshot

snapshot = load_snapshot()
app = Dash(
    __name__,
    title="VantageOps - Python Operations Intelligence",
    update_title=None,
    suppress_callback_exceptions=True,
    assets_folder="assets",
)
server = app.server
register_api(server, snapshot)

app.index_string = """
<!DOCTYPE html>
<html>
  <head>
    {%metas%}
    <meta property="og:title" content="VantageOps - Python Operations Intelligence">
    <meta property="og:description" content="Enterprise analytics, forecasting, risk intelligence, and scenario planning built with Python.">
    <meta property="og:image" content="/assets/og.jpg">
    <meta name="twitter:card" content="summary_large_image">
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
  </head>
  <body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
  </body>
</html>
"""

app.layout = html.Div([dcc.Location(id="url", refresh=False), html.Div(id="app-page")])


@callback(Output("app-page", "children"), Input("url", "pathname"))
def route_page(pathname: str):
    """Render a Python layout for the requested dashboard function."""
    return shell(pathname or "/", snapshot)


@callback(
    Output("scenario-output", "children"),
    Output("demand-change-value", "children"),
    Output("price-change-value", "children"),
    Output("cost-change-value", "children"),
    Output("inventory-change-value", "children"),
    Input("demand-change", "value"),
    Input("price-change", "value"),
    Input("cost-change", "value"),
    Input("inventory-change", "value"),
)
def update_scenario(demand: float, price: float, cost: float, inventory: float):
    """Recalculate scenario outcomes entirely in Python."""
    values = calculate_scenario(snapshot, demand, price, cost, inventory)
    output = html.Div(
        children=[
            html.Div("PROJECTED OUTCOME", className="eyebrow"),
            html.H2("Scenario impact"),
            html.Div(
                className="scenario-metrics",
                children=[
                    kpi_card("Revenue", money(values["revenue"], True), f"{demand + price:+.0f}% commercial lift"),
                    kpi_card(
                        "Gross margin",
                        f"{values['gross_margin_pct']:.1f}%",
                        f"{values['gross_margin_pct'] - snapshot.kpis['gross_margin_pct']:+.1f} pts",
                    ),
                    kpi_card("Working capital", money(values["working_capital"], True), f"{inventory:+.0f}% inventory"),
                    kpi_card("Service level", f"{values['service_level_pct']:.1f}%", "Modelled fulfilment"),
                ],
            ),
            html.Div(
                className="recommendation",
                children=[
                    html.Strong("Decision signal"),
                    html.P(
                        f"This plan changes annual gross profit by {money(values['profit_delta'], True)}. "
                        "Validate the price assumption with Sales before releasing the inventory budget."
                    ),
                ],
            ),
        ]
    )
    labels = tuple(f"{value:+.0f}%" for value in (demand, price, cost, inventory))
    return output, *labels


@callback(
    Output("upload-result", "children"),
    Output("upload-analysis", "children"),
    Input("sales-upload", "contents"),
    State("sales-upload", "filename"),
)
def validate_upload(contents: str | None, filename: str | None):
    """Validate and summarize a user-provided transaction-level sales CSV."""
    if not contents:
        raise PreventUpdate
    try:
        _, encoded = contents.split(",", 1)
        decoded = base64.b64decode(encoded).decode("utf-8-sig")
        frame = pd.read_csv(io.StringIO(decoded))
        result = analyze_uploaded_sales(frame)
        total_revenue = float(result.clean["net_revenue"].sum())
        total_units = float(result.clean["quantity"].sum())
        best_month = result.monthly.loc[result.monthly["net_revenue"].idxmax()]
        preview = result.clean.sort_values("sale_date", ascending=False).head(6)
        status = html.Div(
            className="upload-success",
            children=[
                html.Strong(f"{filename}: monthly sales report ready"),
                html.Span(f"{len(result.clean):,} purchases accepted - {result.rejected_rows:,} rows rejected"),
            ],
        )
        analysis = html.Div(
            className="panel uploaded-report",
            children=[
                html.Div(
                    className="uploaded-report-head",
                    children=[
                        html.Div(
                            children=[
                                html.Div("YOUR UPLOADED DATA", className="eyebrow"),
                                html.H2("Monthly sales report"),
                                html.P("The chart groups every purchase by month and product. Hover over a bar for the exact revenue."),
                            ]
                        ),
                        html.Span("Calculated in Python", className="python-badge"),
                    ],
                ),
                html.Div(
                    className="metrics-grid upload-metrics",
                    children=[
                        kpi_card("Net revenue", money(total_revenue), "After discounts"),
                        kpi_card("Purchases", f"{len(result.clean):,}", "Accepted rows"),
                        kpi_card("Units sold", f"{total_units:,.0f}", "Across all products"),
                        kpi_card(
                            "Best month",
                            best_month["month"].strftime("%b %Y"),
                            money(float(best_month["net_revenue"])),
                        ),
                    ],
                ),
                html.Div(
                    className="upload-report-grid",
                    children=[
                        html.Div(
                            className="upload-chart",
                            children=dcc.Graph(
                                figure=uploaded_sales_figure(result),
                                config={"displayModeBar": False, "responsive": True},
                            ),
                        ),
                        html.Div(
                            className="upload-preview",
                            children=[
                                html.Div("LATEST PURCHASES", className="eyebrow"),
                                html.Table(
                                    children=[
                                        html.Thead(html.Tr([html.Th("Date"), html.Th("Product"), html.Th("Revenue")])),
                                        html.Tbody(
                                            [
                                                html.Tr(
                                                    [
                                                        html.Td(row.sale_date.strftime("%d %b")),
                                                        html.Td(str(row.product)),
                                                        html.Td(money(float(row.net_revenue))),
                                                    ]
                                                )
                                                for row in preview.itertuples()
                                            ]
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        return status, analysis
    except Exception as error:
        return (
            html.Div(
                className="upload-error",
                children=[html.Strong(f"{filename}: report could not be created"), html.Span(str(error))],
            ),
            html.Div(),
        )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
