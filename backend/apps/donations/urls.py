from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DonationCheckoutView,
    DonationProjectViewSet,
    DonationTransactionAdminViewSet,
    DonationVerifyView,
    FlutterwaveWebhookView,
    PayPalWebhookView,
    PaystackWebhookView,
    ResendReceiptView,
)

router = DefaultRouter()
router.register(r"projects", DonationProjectViewSet, basename="donation-project")
router.register(r"admin/transactions", DonationTransactionAdminViewSet, basename="admin-donation-transaction")

urlpatterns = [
    path("checkout/", DonationCheckoutView.as_view(), name="donation-checkout"),
    path("verify/", DonationVerifyView.as_view(), name="donation-verify"),
    path("transactions/<uuid:pk>/resend-receipt/", ResendReceiptView.as_view(), name="donation-resend-receipt"),
    path("webhooks/paystack/", PaystackWebhookView.as_view(), name="webhook-paystack"),
    path("webhooks/flutterwave/", FlutterwaveWebhookView.as_view(), name="webhook-flutterwave"),
    path("webhooks/paypal/", PayPalWebhookView.as_view(), name="webhook-paypal"),
    path("", include(router.urls)),
]
