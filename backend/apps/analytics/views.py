from datetime import timedelta
from django.db.models import Avg, Count
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import PageViewEvent
from .serializers import (
    AnalyticsOverviewResponseSerializer,
    TrackPageViewSerializer,
)
from .utils import (
    PAGE_TITLE_MAP,
    detect_device_type,
    is_bot_user_agent,
    resolve_country,
)


class AnalyticsAnonThrottle(AnonRateThrottle):
    rate = "120/minute"


class TrackPageViewView(APIView):
    """
    Public ingestion endpoint for recording visitor pageviews and active duration.
    Throttled and ignores common crawlers/bots.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AnalyticsAnonThrottle]

    @extend_schema(
        request=TrackPageViewSerializer,
        responses={200: dict},
        description="Record a public page visit or update session duration.",
    )
    def post(self, request):
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if is_bot_user_agent(user_agent):
            return Response({"status": "ignored", "reason": "bot"}, status=status.HTTP_200_OK)

        serializer = TrackPageViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data["sessionId"].strip()
        path = serializer.validated_data["path"].strip()
        title = serializer.validated_data.get("title", "").strip()
        duration_seconds = serializer.validated_data.get("durationSeconds", 0)

        # Do not track internal staff routes
        if path.startswith("/admin") or path.startswith("/control-panel") or path.startswith("/api"):
            return Response({"status": "ignored", "reason": "internal_route"}, status=status.HTTP_200_OK)

        # Clean trailing slash (keep root "/" as is)
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        if not title:
            title = PAGE_TITLE_MAP.get(path, path)

        # If this is a duration update beacon for an existing view on the same path
        if duration_seconds > 0:
            recent_cutoff = timezone.now() - timedelta(minutes=60)
            existing_event = (
                PageViewEvent.objects.filter(
                    session_id=session_id,
                    path=path,
                    created_at__gte=recent_cutoff,
                )
                .order_by("-created_at")
                .first()
            )
            if existing_event:
                if duration_seconds > existing_event.duration_seconds:
                    existing_event.duration_seconds = duration_seconds
                if duration_seconds >= 10:
                    existing_event.is_bounce = False
                existing_event.save(update_fields=["duration_seconds", "is_bounce"])
                return Response({"status": "updated"}, status=status.HTTP_200_OK)

        # Fresh pageview
        device_type = detect_device_type(user_agent)
        country_code, country_name = resolve_country(request)

        # Multi-page check
        has_prior = PageViewEvent.objects.filter(session_id=session_id).exists()
        if has_prior:
            is_bounce = False
            # Retroactively mark prior session pages as not bounced
            PageViewEvent.objects.filter(session_id=session_id, is_bounce=True).update(is_bounce=False)
        else:
            is_bounce = True

        PageViewEvent.objects.create(
            session_id=session_id,
            path=path,
            title=title,
            country_code=country_code,
            country_name=country_name,
            device_type=device_type,
            duration_seconds=duration_seconds,
            is_bounce=is_bounce,
        )

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class AnalyticsOverviewView(APIView):
    """
    Authenticated administrative endpoint returning aggregated metrics
    matching the AdminAnalyticsPage dashboard layout.
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="range", description="Time window (7D, 30D, 90D)", required=False, type=str),
        ],
        responses={200: AnalyticsOverviewResponseSerializer},
        description="Retrieve site visitation statistics, charts, geographic and device distributions.",
    )
    def get(self, request):
        time_range = request.query_params.get("range", "7D").upper()
        days_map = {"7D": 7, "30D": 30, "90D": 90}
        days = days_map.get(time_range, 7)

        now = timezone.now()
        start_date = now - timedelta(days=days)

        events = PageViewEvent.objects.filter(created_at__gte=start_date)
        total_pageviews = events.count()

        if total_pageviews == 0:
            empty_data = {
                "totalPageviews": 0,
                "uniqueVisitors": 0,
                "avgSessionSeconds": 0,
                "bounceRate": 0.0,
                "dailyVisits": [],
                "topPages": [],
                "countries": [],
                "devices": [],
            }
            return Response(empty_data, status=status.HTTP_200_OK)

        unique_visitors = events.values("session_id").distinct().count()

        avg_dur_dict = events.filter(duration_seconds__gt=0).aggregate(avg=Avg("duration_seconds"))
        avg_session_seconds = int(round(avg_dur_dict["avg"] or 0))

        # Bounce rate: sessions with single pageview and marked bounce
        bounced_sessions = (
            events.filter(is_bounce=True)
            .values("session_id")
            .distinct()
            .count()
        )
        bounce_rate = round((bounced_sessions / max(1, unique_visitors)) * 100, 1)

        # Daily visitation volume
        # Generate all calendar days in range up to today
        daily_visits = []
        for d_offset in range(days - 1, -1, -1):
            day_target = (now - timedelta(days=d_offset)).date()
            day_events = events.filter(created_at__date=day_target)
            day_views = day_events.count()
            day_unique = day_events.values("session_id").distinct().count()
            daily_visits.append({
                "date": day_target.strftime("%b %d"),
                "visits": day_unique,
                "pageviews": day_views,
            })

        # Top engaging pages
        page_counts = (
            events.values("path", "title")
            .annotate(views=Count("id"))
            .order_by("-views")[:10]
        )
        top_pages = []
        for p in page_counts:
            path_str = p["path"]
            title_str = p["title"] or PAGE_TITLE_MAP.get(path_str, path_str)
            views_count = p["views"]
            top_pages.append({
                "path": path_str,
                "title": title_str,
                "views": views_count,
                "pct": int(round((views_count / max(1, total_pageviews)) * 100)),
            })

        # Geographic distribution (unique visitors per country)
        country_counts = (
            events.values("country_code", "country_name")
            .annotate(visitors=Count("session_id", distinct=True))
            .order_by("-visitors")[:6]
        )
        countries = []
        for c in country_counts:
            c_name = c["country_name"] or "Global / Unknown"
            c_code = c["country_code"] or "XX"
            v_count = c["visitors"]
            countries.append({
                "name": c_name,
                "code": c_code,
                "visitors": v_count,
                "pct": int(round((v_count / max(1, unique_visitors)) * 100)),
            })

        # Platform & Device breakdown
        device_counts = (
            events.values("device_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        device_label_map = {
            "mobile": "Mobile Devices (iOS & Android)",
            "desktop": "Desktop & Laptop Browsers",
            "tablet": "Tablets & Large Displays",
        }
        devices = []
        for dev in device_counts:
            dev_type = dev["device_type"]
            count = dev["count"]
            devices.append({
                "type": device_label_map.get(dev_type, dev_type.capitalize()),
                "pct": int(round((count / max(1, total_pageviews)) * 100)),
                "count": count,
            })

        # Ensure all 3 device categories exist in response for UI completeness
        existing_types = {d["type"] for d in devices}
        for key, label in device_label_map.items():
            if label not in existing_types:
                devices.append({
                    "type": label,
                    "pct": 0,
                    "count": 0,
                })

        data = {
            "totalPageviews": total_pageviews,
            "uniqueVisitors": unique_visitors,
            "avgSessionSeconds": avg_session_seconds,
            "bounceRate": bounce_rate,
            "dailyVisits": daily_visits,
            "topPages": top_pages,
            "countries": countries,
            "devices": devices,
        }
        return Response(data, status=status.HTTP_200_OK)
