import threading

from django.db.models import Q
from django.utils import timezone
from rest_framework import parsers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminOrReadOnly

from .models import AutoPublishSettings, Devotional, DevotionalBatch, DevotionalParsedEntry
from .serializers import (
    AutoPublishSettingsSerializer,
    DevotionalBatchDetailSerializer,
    DevotionalBatchSerializer,
    DevotionalCalendarSerializer,
    DevotionalParsedEntrySerializer,
    DevotionalSerializer,
    DevotionalUploadSerializer,
)
from .tasks import check_and_auto_publish_devotionals, confirm_and_import_batch, run_batch_parsing


class DevotionalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = DevotionalSerializer
    lookup_field = "date"

    def get_queryset(self):
        user = self.request.user
        qs = Devotional.objects.all() if (user and user.is_authenticated and user.is_staff) else Devotional.objects.published()

        # Query filters
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(text_reference__icontains=search)
                | Q(key_verse_text__icontains=search)
                | Q(reflection_body__icontains=search)
                | Q(author_attribution__icontains=search)
            )

        status_param = self.request.query_params.get("status")
        if status_param and user and user.is_authenticated and user.is_staff:
            qs = qs.filter(status=status_param.upper())

        batch_id = self.request.query_params.get("batch")
        if batch_id:
            qs = qs.filter(batch_id=batch_id)

        return qs

    def get_object(self):
        # Support lookup by UUID id or by date string YYYY-MM-DD
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        val = self.kwargs[lookup_url_kwarg]
        qs = self.get_queryset()
        try:
            return qs.get(id=val)
        except Exception:
            return super().get_object()

    @action(detail=False, methods=["get"], url_path=r"calendar/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})")
    def calendar(self, request, year=None, month=None):
        """
        Returns lightweight devotional entries for a specific year and month.
        """
        user = request.user
        qs = Devotional.objects.all() if (user and user.is_authenticated and user.is_staff) else Devotional.objects.published()
        qs = qs.filter(date__year=int(year), date__month=int(month)).order_by("date")
        serializer = DevotionalCalendarSerializer(qs, many=True)
        return Response({"success": True, "results": serializer.data})


class TodayDevotionalView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        # Ensure pending auto-publishes run
        try:
            check_and_auto_publish_devotionals()
        except Exception:
            pass

        today = timezone.localdate()
        devotional = Devotional.objects.published().filter(date=today).first()
        if not devotional:
            # Fallback to the latest available published devotional if today isn't published yet
            devotional = Devotional.objects.published().order_by("-date").first()

        if not devotional:
            return Response(
                {"success": False, "message": "No devotionals currently available."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"success": True, "data": DevotionalSerializer(devotional).data})


class DevotionalBatchViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        return DevotionalBatch.objects.all()

    def get_serializer_class(self):
        if self.action in ["retrieve"]:
            return DevotionalBatchDetailSerializer
        return DevotionalBatchSerializer

    def create(self, request, *args, **kwargs):
        upload_serializer = DevotionalUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)

        uploaded_file = upload_serializer.validated_data["file"]
        target_year = upload_serializer.validated_data.get("target_year", 2026)
        start_page = upload_serializer.validated_data.get("start_page", 1)
        end_page = upload_serializer.validated_data.get("end_page", 184)

        batch = DevotionalBatch.objects.create(
            file_name=uploaded_file.name,
            file=uploaded_file,
            target_year=target_year,
            start_page=start_page,
            end_page=end_page,
            status="UPLOADING",
            uploaded_by=request.user,
        )

        # Run parsing in background thread to return fast while extracting
        def run_async():
            run_batch_parsing(str(batch.id))

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

        batch_serializer = DevotionalBatchSerializer(batch)
        return Response(
            {
                "success": True,
                "message": "File uploaded successfully. Parsing started in background.",
                "data": batch_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        batch = self.get_object()
        replace_conflicts = request.data.get("replace_conflicts", True)

        try:
            imported_count = confirm_and_import_batch(str(batch.id), replace_conflicts=replace_conflicts)
            return Response(
                {
                    "success": True,
                    "message": f"Successfully imported {imported_count} devotionals into drafts.",
                    "imported_count": imported_count,
                }
            )
        except Exception as e:
            return Response(
                {"success": False, "message": f"Import failed: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DevotionalParsedEntryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = DevotionalParsedEntry.objects.all()
    serializer_class = DevotionalParsedEntrySerializer


class AutoPublishSettingsView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        settings_obj = AutoPublishSettings.load()
        serializer = AutoPublishSettingsSerializer(settings_obj)
        return Response({"success": True, "data": serializer.data})

    def put(self, request):
        if not (request.user and request.user.is_authenticated and request.user.is_staff):
            return Response({"success": False, "message": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)

        settings_obj = AutoPublishSettings.load()
        serializer = AutoPublishSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        # Check and run auto-publish immediately if enabled
        check_and_auto_publish_devotionals()
        return Response({"success": True, "data": serializer.data})
