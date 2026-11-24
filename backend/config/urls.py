"""
URL Configuration for HOREMOW backend.
All APIs are versioned under /api/v1/
"""

from apps.ministry.views import SitemapXmlView
from common.views import health_check, readiness_check
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1_patterns = [
    # Health and readiness
    path("health/", health_check, name="health-check"),
    path("ready/", readiness_check, name="readiness-check"),
    # Documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Domain Endpoints
    path("auth/", include("apps.accounts.urls")),
    path("audit/", include("apps.audit.urls")),
    path("ministry/", include("apps.ministry.urls")),
    path("sermons/", include("apps.sermons.urls")),
    path("devotionals/", include("apps.devotionals.urls")),
    path("events/", include("apps.events.urls")),
    path("publications/", include("apps.publications.urls")),
    path("posts/", include("apps.blog.urls")),
    path("locations/", include("apps.locations.urls")),
    path("donations/", include("apps.donations.urls")),
    path("contact/", include("apps.contact.urls")),
    path("media/", include("apps.media_library.urls")),
    path("analytics/", include("apps.analytics.urls")),
]

urlpatterns = [
    # SEO XML Sitemap
    path("sitemap.xml", SitemapXmlView.as_view(), name="root-sitemap"),
    # Private Django Admin (can be customized/disabled or mapped to a secure path)
    path("control-panel/", admin.site.urls),
    # REST API v1
    path("api/v1/", include(api_v1_patterns)),
]

# Ensure uploaded media files (such as local fallback publication PDFs) can be served in production
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

handler404 = "common.views.custom_404_view"
handler500 = "common.views.custom_500_view"
