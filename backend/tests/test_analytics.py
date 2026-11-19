import pytest
from apps.accounts.models import User
from apps.analytics.models import PageViewEvent
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_track_pageview_success():
    client = APIClient()
    payload = {
        "sessionId": "test-session-12345",
        "path": "/sermons",
        "title": "Audio & Video Sermons",
    }
    response = client.post(
        "/api/v1/analytics/track/",
        payload,
        format="json",
        HTTP_USER_AGENT="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
        HTTP_CF_IPCOUNTRY="NG",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    event = PageViewEvent.objects.filter(session_id="test-session-12345").first()
    assert event is not None
    assert event.path == "/sermons"
    assert event.title == "Audio & Video Sermons"
    assert event.device_type == "mobile"
    assert event.country_code == "NG"
    assert event.country_name == "Nigeria"
    assert event.is_bounce is True


@pytest.mark.django_db
def test_track_pageview_duration_update():
    client = APIClient()
    session_id = "test-session-update"

    # Initial view
    client.post(
        "/api/v1/analytics/track/",
        {"sessionId": session_id, "path": "/devotional"},
        format="json",
        HTTP_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    )
    event = PageViewEvent.objects.get(session_id=session_id)
    assert event.duration_seconds == 0
    assert event.is_bounce is True

    # Duration beacon update
    response = client.post(
        "/api/v1/analytics/track/",
        {"sessionId": session_id, "path": "/devotional", "durationSeconds": 45},
        format="json",
        HTTP_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "updated"

    event.refresh_from_db()
    assert event.duration_seconds == 45
    assert event.is_bounce is False  # 45s > 10s clears bounce


@pytest.mark.django_db
def test_track_multipage_session_clears_bounce():
    client = APIClient()
    session_id = "test-session-multi"

    client.post(
        "/api/v1/analytics/track/",
        {"sessionId": session_id, "path": "/"},
        format="json",
    )
    first_event = PageViewEvent.objects.get(session_id=session_id, path="/")
    assert first_event.is_bounce is True

    client.post(
        "/api/v1/analytics/track/",
        {"sessionId": session_id, "path": "/about"},
        format="json",
    )
    first_event.refresh_from_db()
    second_event = PageViewEvent.objects.get(session_id=session_id, path="/about")
    assert first_event.is_bounce is False
    assert second_event.is_bounce is False


@pytest.mark.django_db
def test_bot_and_internal_routes_ignored():
    client = APIClient()

    # Crawler/bot ignored
    res_bot = client.post(
        "/api/v1/analytics/track/",
        {"sessionId": "bot-session", "path": "/sermons"},
        format="json",
        HTTP_USER_AGENT="Googlebot/2.1 (+http://www.google.com/bot.html)",
    )
    assert res_bot.status_code == 200
    assert res_bot.json()["status"] == "ignored"
    assert not PageViewEvent.objects.filter(session_id="bot-session").exists()

    # Admin route ignored
    res_admin = client.post(
        "/api/v1/analytics/track/",
        {"sessionId": "staff-session", "path": "/admin/analytics"},
        format="json",
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["status"] == "ignored"
    assert not PageViewEvent.objects.filter(session_id="staff-session").exists()


@pytest.mark.django_db
def test_analytics_overview_permissions_and_stats():
    client = APIClient()

    # Anonymous access blocked
    res_anon = client.get("/api/v1/analytics/overview/")
    assert res_anon.status_code in [401, 403]

    # Non-staff user blocked
    member = User.objects.create_user(email="member@horemow.org", password="Password123!", is_staff=False)
    client.force_authenticate(user=member)
    res_member = client.get("/api/v1/analytics/overview/")
    assert res_member.status_code == 403

    # Staff/Admin user allowed
    admin_user = User.objects.create_user(email="admin@horemow.org", password="Password123!", is_staff=True)
    client.force_authenticate(user=admin_user)
    res_empty = client.get("/api/v1/analytics/overview/?range=7D")
    assert res_empty.status_code == 200
    assert res_empty.json()["totalPageviews"] == 0
    assert res_empty.json()["uniqueVisitors"] == 0

    # Seed events
    PageViewEvent.objects.create(
        session_id="s1",
        path="/",
        title="Homepage & Video Emblem",
        country_code="NG",
        country_name="Nigeria",
        device_type="mobile",
        duration_seconds=60,
        is_bounce=False,
    )
    PageViewEvent.objects.create(
        session_id="s1",
        path="/sermons",
        title="Audio & Video Sermons",
        country_code="NG",
        country_name="Nigeria",
        device_type="mobile",
        duration_seconds=120,
        is_bounce=False,
    )
    PageViewEvent.objects.create(
        session_id="s2",
        path="/give",
        title="Donations & Giving Portal",
        country_code="US",
        country_name="United States",
        device_type="desktop",
        duration_seconds=30,
        is_bounce=True,
    )

    res_stats = client.get("/api/v1/analytics/overview/?range=7D")
    assert res_stats.status_code == 200
    data = res_stats.json()

    assert data["totalPageviews"] == 3
    assert data["uniqueVisitors"] == 2
    assert len(data["dailyVisits"]) == 7
    assert len(data["topPages"]) >= 2
    assert any(c["name"] == "Nigeria" for c in data["countries"])
    assert any(d["type"].startswith("Mobile") for d in data["devices"])
