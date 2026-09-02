from app import server


def test_health_endpoint_identifies_python_service():
    client = server.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {
        "service": "vantageops-python-api",
        "status": "healthy",
    }


def test_business_api_endpoints_return_data():
    client = server.test_client()
    for path in ("/api/kpis", "/api/forecast", "/api/risks", "/api/pipeline"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.get_json()
