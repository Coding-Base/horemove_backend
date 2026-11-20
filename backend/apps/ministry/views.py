from datetime import datetime
from common.api.mixins import AuditedModelViewSetMixin
from common.permissions import IsAdminOrReadOnly
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Doctrine, HomepageSection, Leader, MinistryProfile
from .serializers import (
    DoctrineSerializer,
    HomepageSectionSerializer,
    LeaderSerializer,
    MinistryProfileSerializer,
)


class MinistryProfileView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def _get_profile(self):
        profile = MinistryProfile.objects.first()
        if not profile:
            profile = MinistryProfile.objects.create(
                id="00000000-0000-0000-0000-000000000001",
                name="Holiness Revival Movement Worldwide",
                acronym="HOREMOW",
                motto="Holiness without which no man shall see the Lord",
            )
        return profile

    def get(self, request):
        profile = self._get_profile()
        return Response({"success": True, "data": MinistryProfileSerializer(profile).data})

    def put(self, request):
        return self._save(request, partial=False)

    def patch(self, request):
        return self._save(request, partial=True)

    def _save(self, request, partial=True):
        profile = self._get_profile()
        serializer = MinistryProfileSerializer(profile, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})


class LeaderViewSet(AuditedModelViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = LeaderSerializer

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated and self.request.user.is_staff:
            return Leader.objects.all()
        return Leader.objects.filter(is_active=True)


class DoctrineViewSet(AuditedModelViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = DoctrineSerializer

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated and self.request.user.is_staff:
            return Doctrine.objects.all()
        return Doctrine.objects.filter(is_active=True)


class HomepageSectionViewSet(AuditedModelViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = HomepageSectionSerializer
    lookup_field = "section_key"

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated and self.request.user.is_staff:
            return HomepageSection.objects.all()
        return HomepageSection.objects.filter(is_active=True)


class SitemapXmlView(APIView):
    """
    Generates and returns standard XML sitemap for SEO crawlers (Google, Bing).
    Includes all static pages and dynamic published blog posts.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        origin = request.headers.get("Origin") or request.build_absolute_uri("/").rstrip("/")
        if "api" in origin or "127.0.0.1" in origin or "localhost" in origin:
            site_domain = "https://horemow.org"
        else:
            site_domain = origin

        static_routes = [
            ("", "1.0", "daily"),
            ("about", "0.8", "monthly"),
            ("sermons", "0.9", "weekly"),
            ("devotional", "0.9", "daily"),
            ("events", "0.8", "weekly"),
            ("locations", "0.8", "monthly"),
            ("directory", "0.7", "monthly"),
            ("bookstore", "0.8", "weekly"),
            ("gallery", "0.7", "monthly"),
            ("give", "0.9", "monthly"),
            ("blog", "0.9", "daily"),
            ("broadcasts", "0.7", "weekly"),
            ("contact", "0.8", "monthly"),
        ]

        now_str = datetime.now().strftime("%Y-%m-%d")
        xml_entries = []
        for route, priority, changefreq in static_routes:
            url = f"{site_domain}/{route}".rstrip("/")
            xml_entries.append(
                f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{now_str}</lastmod>\n    <changefreq>{changefreq}</changefreq>\n    <priority>{priority}</priority>\n  </url>"
            )

        try:
            from apps.blog.models import Post

            for post in Post.objects.filter(status="PUBLISHED")[:100]:
                post_mod = post.updated_at.strftime("%Y-%m-%d")
                xml_entries.append(
                    f"  <url>\n    <loc>{site_domain}/blog/{post.slug}</loc>\n    <lastmod>{post_mod}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>"
                )
        except Exception:
            pass

        xml_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(xml_entries)
            + "\n</urlset>"
        )
        return HttpResponse(xml_content, content_type="application/xml")
