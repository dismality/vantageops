"""JSON API routes for VantageOps analytics."""

from flask import Flask, jsonify

from pipeline.dashboard_data import DashboardSnapshot


def register_api(server: Flask, snapshot: DashboardSnapshot) -> None:
    """Attach read-only business endpoints to the Dash Flask server."""

    @server.get("/api/health")
    def health():
        return jsonify({"status": "healthy", "service": "vantageops-python-api"})

    @server.get("/api/kpis")
    def kpis():
        return jsonify({key: round(value, 2) for key, value in snapshot.kpis.items()})

    @server.get("/api/forecast")
    def forecast():
        records = snapshot.forecast.copy()
        records["month"] = records["month"].dt.strftime("%Y-%m-%d")
        return jsonify(records.round(2).to_dict(orient="records"))

    @server.get("/api/risks")
    def risks():
        return jsonify(snapshot.alerts)

    @server.get("/api/pipeline")
    def pipeline():
        return jsonify(
            {
                "source_rows": snapshot.source_rows,
                "accepted_rows": snapshot.accepted_rows,
                "quarantined_rows": snapshot.quarantined_rows,
                "quality_checks": snapshot.quality_checks,
            }
        )
