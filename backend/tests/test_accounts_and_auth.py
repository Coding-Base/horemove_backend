import pytest
from apps.accounts.models import User
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_user_creation_and_jwt_login():
    User.objects.create_user(
        email="editor@horemow.org",
        password="SuperSecretPassword123!",
        first_name="John",
        last_name="Doe",
        role="CONTENT_EDITOR",
    )

    client = APIClient()
    # Attempt login with correct password
    response = client.post(
        "/api/v1/auth/login/",
        {"email": "editor@horemow.org", "password": "SuperSecretPassword123!"},
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "tokens" in data
    assert "access" in data["tokens"]
    assert "refresh" in data["tokens"]
    assert data["user"]["email"] == "editor@horemow.org"

    # Authenticated access to /api/v1/auth/me/
    access_token = data["tokens"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    me_response = client.get("/api/v1/auth/me/")
    assert me_response.status_code == 200
    assert me_response.json()["user"]["role"] == "CONTENT_EDITOR"


@pytest.mark.django_db
def test_invalid_login_and_lockout():
    user = User.objects.create_user(
        email="target@horemow.org",
        password="ValidPassword123!",
    )
    client = APIClient()

    # Fail 3 times
    for _ in range(3):
        client.post(
            "/api/v1/auth/login/",
            {"email": "target@horemow.org", "password": "WrongPassword"},
            format="json",
        )

    user.refresh_from_db()
    assert user.failed_login_attempts >= 3
    assert user.is_locked is True

    # 4th attempt should be blocked by account lockout
    res = client.post(
        "/api/v1/auth/login/",
        {"email": "target@horemow.org", "password": "ValidPassword123!"},
        format="json",
    )
    assert res.status_code == 400
    assert "locked" in str(res.json())


@pytest.mark.django_db
def test_subadmin_provisioning_restricted_to_superadmin():
    editor = User.objects.create_user(
        email="editor2@horemow.org",
        password="EditorPassword123!",
        role="CONTENT_EDITOR",
        is_staff=True,
    )
    superadmin = User.objects.create_superuser(
        email="admin@horemow.org",
        password="AdminPassword123!",
    )

    client = APIClient()

    # Content editor cannot access sub-admin provisioning
    client.force_authenticate(user=editor)
    res_forbidden = client.get("/api/v1/auth/users/")
    assert res_forbidden.status_code == 403

    # SuperAdmin can access and provision users
    client.force_authenticate(user=superadmin)
    res_ok = client.get("/api/v1/auth/users/")
    assert res_ok.status_code == 200


@pytest.mark.django_db
def test_superadmin_registration_requires_valid_auth_code(settings):
    cache.clear()
    settings.SUPERADMIN_REGISTRATION_CODE = "SecretSetupPasscode123!"
    client = APIClient()

    payload = {
        "email": "director@horemow.org",
        "password": "StrongPassword2026!",
        "first_name": "Paul",
        "last_name": "Rika",
    }

    # 1. Missing auth_code -> 403 Forbidden
    res_missing = client.post("/api/v1/auth/register/", payload, format="json")
    assert res_missing.status_code == 403
    assert "Invalid authentication code" in res_missing.json()["message"]

    # 2. Wrong auth_code -> 403 Forbidden
    payload["auth_code"] = "WrongCode"
    res_wrong = client.post("/api/v1/auth/register/", payload, format="json")
    assert res_wrong.status_code == 403
    assert "Invalid authentication code" in res_wrong.json()["message"]

    # 3. Valid auth_code -> 201 Created with tokens & superadmin privileges
    payload["auth_code"] = "SecretSetupPasscode123!"
    res_success = client.post("/api/v1/auth/register/", payload, format="json")
    assert res_success.status_code == 201
    data = res_success.json()
    assert data["success"] is True
    assert "tokens" in data
    assert data["user"]["email"] == "director@horemow.org"
    assert data["user"]["role"] == "SUPERADMIN"

    user = User.objects.get(email="director@horemow.org")
    assert user.is_superuser is True
    assert user.is_staff is True
    assert "*" in user.capabilities


@pytest.mark.django_db
def test_superadmin_registration_disabled_when_code_not_set(settings):
    cache.clear()
    settings.SUPERADMIN_REGISTRATION_CODE = ""
    client = APIClient()

    payload = {
        "email": "director2@horemow.org",
        "password": "StrongPassword2026!",
        "auth_code": "SomeAttempt",
    }
    res = client.post("/api/v1/auth/register/", payload, format="json")
    assert res.status_code == 403
    assert "disabled" in res.json()["message"].lower()
