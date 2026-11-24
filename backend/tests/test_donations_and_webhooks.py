import hashlib
import hmac
import json
from decimal import Decimal

import pytest
from apps.accounts.models import User
from apps.donations.models import DonationProject, DonationTransaction
from django.conf import settings
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_donation_checkout_captures_email_and_generates_reference():
    project = DonationProject.objects.create(
        name="Global Bible Translation",
        slug="bible-translation",
        description="Translating holy literature into African and Asian languages",
        currency="NGN",
    )

    client = APIClient()
    payload = {
        "project_id": str(project.id),
        "amount": "5000.00",
        "currency": "NGN",
        "donor_name": "Sister Deborah",
        "donor_email": "deborah@example.com",
        "provider": "PAYSTACK",
    }
    response = client.post("/api/v1/donations/checkout/", payload, format="json")
    assert response.status_code == 201
    data = response.json()["data"]
    assert "reference" in data
    assert data["donor_email"] == "deborah@example.com"
    assert data["amount"] == "5000.00"

    # Transaction in DB is PENDING
    tx = DonationTransaction.objects.get(provider_reference=data["reference"])
    assert tx.status == "PENDING"
    assert tx.donor_email == "deborah@example.com"


@pytest.mark.django_db
def test_paystack_webhook_invalid_signature_is_rejected():
    client = APIClient()
    fake_body = json.dumps({"event": "charge.success", "data": {"reference": "test"}})
    response = client.post(
        "/api/v1/donations/webhooks/paystack/",
        data=fake_body,
        content_type="application/json",
        HTTP_X_PAYSTACK_SIGNATURE="invalid-forged-signature",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_paystack_webhook_valid_signature_processes_and_sends_appreciation_email(mailoutbox):
    tx = DonationTransaction.objects.create(
        amount=Decimal("15000.00"),
        currency="NGN",
        donor_name="Brother Timothy",
        donor_email="timothy@example.com",
        provider="PAYSTACK",
        provider_reference="HRMW-PSTK-TESTREF001",
        idempotency_key="IDEMP-001",
        status="PENDING",
    )

    webhook_payload = {
        "event": "charge.success",
        "data": {
            "reference": "HRMW-PSTK-TESTREF001",
            "amount": 1500000,  # 15,000 NGN in kobo
            "currency": "NGN",
            "status": "success",
        },
    }
    raw_body = json.dumps(webhook_payload).encode("utf-8")
    valid_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    client = APIClient()
    response = client.post(
        "/api/v1/donations/webhooks/paystack/",
        data=raw_body,
        content_type="application/json",
        HTTP_X_PAYSTACK_SIGNATURE=valid_signature,
    )
    assert response.status_code == 200

    tx.refresh_from_db()
    assert tx.status == "SUCCESSFUL"
    assert tx.appreciation_email_sent is True

    # Verify donor appreciation email was dispatched to mailoutbox
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert "timothy@example.com" in email.to
    assert "HRMW-PSTK-TESTREF001" in email.subject
    assert "Brother Timothy" in email.body
    assert "15,000.00" in email.body


@pytest.mark.django_db
def test_financial_ledger_role_permission_gating():
    DonationTransaction.objects.create(
        amount=Decimal("500.00"),
        currency="USD",
        donor_name="Sister Grace",
        donor_email="grace@example.com",
        provider="PAYPAL",
        provider_reference="HRMW-PYPL-TESTREF002",
        idempotency_key="IDEMP-002",
        status="SUCCESSFUL",
    )

    editor = User.objects.create_user(
        email="editor@horemow.org",
        password="PassWord123!",
        role="CONTENT_EDITOR",
        is_staff=True,
    )
    finance_auditor = User.objects.create_user(
        email="finance@horemow.org",
        password="PassWord123!",
        role="FINANCE_AUDITOR",
        is_staff=True,
    )

    client = APIClient()

    # Content Editor cannot view financial transactions
    client.force_authenticate(user=editor)
    res_forbidden = client.get("/api/v1/donations/admin/transactions/")
    assert res_forbidden.status_code == 403

    # Finance Auditor can view transactions
    client.force_authenticate(user=finance_auditor)
    res_ok = client.get("/api/v1/donations/admin/transactions/")
    assert res_ok.status_code == 200
    assert res_ok.json()["count"] >= 1

    # Finance Auditor can export transactions to CSV, creating an audit log
    from apps.audit.models import AuditLog

    res_export = client.get("/api/v1/donations/admin/transactions/export/")
    assert res_export.status_code == 200
    assert res_export.headers["Content-Type"] == "text/csv"
    assert "HRMW-PYPL-TESTREF002" in res_export.content.decode("utf-8")

    # Verify audit log entry was created
    audit = AuditLog.objects.filter(action="EXPORT", resource_type="DonationTransaction").first()
    assert audit is not None
    assert audit.actor == finance_auditor
    assert audit.details["exported_records"] >= 1


@pytest.mark.django_db
def test_flutterwave_donation_checkout_initialization():
    project = DonationProject.objects.create(
        name="Global Missions & Evangelical Outreach",
        slug="global-missions-flw",
        description="Global crusade evangelism across Africa and Europe",
        currency="USD",
    )

    client = APIClient()
    payload = {
        "project_id": str(project.id),
        "amount": "100.00",
        "currency": "USD",
        "donor_name": "Brother Paul",
        "donor_email": "paul@example.com",
        "provider": "FLUTTERWAVE",
    }
    response = client.post("/api/v1/donations/checkout/", payload, format="json")
    assert response.status_code == 201
    data = response.json()["data"]
    assert "reference" in data
    assert data["reference"].startswith("HRMW-FLW-")
    assert data["donor_email"] == "paul@example.com"
    assert data["amount"] == "100.00"
    assert data["currency"] == "USD"
    assert "authorization_url" in data

    tx = DonationTransaction.objects.get(provider_reference=data["reference"])
    assert tx.status == "PENDING"
    assert tx.provider == "FLUTTERWAVE"
    assert tx.currency == "USD"


@pytest.mark.django_db
def test_flutterwave_webhook_invalid_hash_is_rejected():
    client = APIClient()
    fake_body = json.dumps({"event": "charge.completed", "data": {"tx_ref": "HRMW-FLW-TEST001"}})
    response = client.post(
        "/api/v1/donations/webhooks/flutterwave/",
        data=fake_body,
        content_type="application/json",
        HTTP_VERIF_HASH="invalid-forged-hash",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_flutterwave_webhook_valid_hash_processes_and_sends_appreciation_email(mailoutbox):
    tx = DonationTransaction.objects.create(
        amount=Decimal("250.00"),
        currency="USD",
        donor_name="Sister Sarah",
        donor_email="sarah@example.com",
        provider="FLUTTERWAVE",
        provider_reference="HRMW-FLW-TESTREF002",
        idempotency_key="IDEMP-FLW-002",
        status="PENDING",
    )

    webhook_payload = {
        "event": "charge.completed",
        "data": {
            "tx_ref": "HRMW-FLW-TESTREF002",
            "amount": 250.00,
            "currency": "USD",
            "status": "successful",
        },
    }
    raw_body = json.dumps(webhook_payload).encode("utf-8")
    secret_hash = getattr(settings, "FLW_SECRET_HASH", "sghfgjjtscjkbcsadjkgdSfjmkg")

    client = APIClient()
    response = client.post(
        "/api/v1/donations/webhooks/flutterwave/",
        data=raw_body,
        content_type="application/json",
        HTTP_VERIF_HASH=secret_hash,
    )
    assert response.status_code == 200

    tx.refresh_from_db()
    assert tx.status == "SUCCESSFUL"
    assert tx.appreciation_email_sent is True

    # Verify donor appreciation email was dispatched to mailoutbox
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert "sarah@example.com" in email.to
    assert "HRMW-FLW-TESTREF002" in email.subject
    assert "Sister Sarah" in email.body
    assert "250.00" in email.body


@pytest.mark.django_db
def test_flutterwave_payment_verification_endpoint(mailoutbox):
    tx = DonationTransaction.objects.create(
        amount=Decimal("50.00"),
        currency="GBP",
        donor_name="Brother Peter",
        donor_email="peter@example.com",
        provider="FLUTTERWAVE",
        provider_reference="HRMW-FLW-TESTREF003",
        idempotency_key="IDEMP-FLW-003",
        status="PENDING",
    )

    client = APIClient()
    response = client.post(
        "/api/v1/donations/verify/",
        data={
            "reference": "HRMW-FLW-TESTREF003",
            "provider": "FLUTTERWAVE",
        },
        format="json",
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True

    tx.refresh_from_db()
    assert tx.status == "SUCCESSFUL"
    assert tx.appreciation_email_sent is True
    assert len(mailoutbox) == 1
    assert "peter@example.com" in mailoutbox[0].to
