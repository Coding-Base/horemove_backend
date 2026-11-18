import pytest
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_returns_200():
    client = APIClient()
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "horemow-backend"}
    assert "X-Request-ID" in response.headers


@pytest.mark.django_db
def test_readiness_check_returns_200():
    client = APIClient()
    response = client.get("/api/v1/ready/")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "connected"}


@pytest.mark.django_db
def test_security_headers_present():
    client = APIClient()
    response = client.get("/api/v1/health/")
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_not_found_returns_standard_error_envelope():
    client = APIClient()
    response = client.get("/api/v1/non-existent-route/")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
    assert "request_id" in data
