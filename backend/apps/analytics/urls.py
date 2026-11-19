from django.urls import path
from .views import AnalyticsOverviewView, TrackPageViewView

app_name = "analytics"

urlpatterns = [
    path("track/", TrackPageViewView.as_view(), name="track-pageview"),
    path("overview/", AnalyticsOverviewView.as_view(), name="analytics-overview"),
]
