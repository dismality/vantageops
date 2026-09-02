"""VantageOps: a Python-first enterprise analytics dashboard and API."""

import base64
import io

import pandas as pd
from dash import Dash, Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate

from api import register_api
from dashboard_views import kpi_card, money, shell
from pipeline.analytics import validate_sales
from pipeline.dashboard_data import calculate_scenario, load_snapshot
from pipeline.generate_sample_data import PRODUCTS

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
    Input("sales-upload", "contents"),
    State("sales-upload", "filename"),
)
def validate_upload(contents: str | None, filename: str | None):
    """Validate a user-provided CSV in memory using the production rules."""
    if not contents:
        raise PreventUpdate
    try:
        _, encoded = contents.split(",", 1)
        frame = pd.read_csv(io.StringIO(base64.b64decode(encoded).decode("utf-8")))
        result = validate_sales(frame, PRODUCTS)
        return html.Div(
            className="upload-success",
            children=[
                html.Strong(f"{filename}: validation complete"),
                html.Span(f"{len(result.clean):,} rows accepted - {len(result.quarantined):,} quarantined"),
            ],
        )
    except Exception as error:
        return html.Div(
            className="upload-error",
            children=[html.Strong(f"{filename}: validation failed"), html.Span(str(error))],
        )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
