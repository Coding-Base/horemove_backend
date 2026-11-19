from rest_framework import serializers


class TrackPageViewSerializer(serializers.Serializer):
    sessionId = serializers.CharField(max_length=64, required=True)
    path = serializers.CharField(max_length=255, required=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    durationSeconds = serializers.IntegerField(required=False, min_value=0, default=0)
    isExit = serializers.BooleanField(required=False, default=False)


class DailyVisitItemSerializer(serializers.Serializer):
    date = serializers.CharField()
    visits = serializers.IntegerField()
    pageviews = serializers.IntegerField()


class TopPageItemSerializer(serializers.Serializer):
    path = serializers.CharField()
    title = serializers.CharField()
    views = serializers.IntegerField()
    pct = serializers.IntegerField()


class CountryItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()
    visitors = serializers.IntegerField()
    pct = serializers.IntegerField()


class DeviceItemSerializer(serializers.Serializer):
    type = serializers.CharField()
    pct = serializers.IntegerField()
    count = serializers.IntegerField()


class AnalyticsOverviewResponseSerializer(serializers.Serializer):
    totalPageviews = serializers.IntegerField()
    uniqueVisitors = serializers.IntegerField()
    avgSessionSeconds = serializers.IntegerField()
    bounceRate = serializers.FloatField()
    dailyVisits = DailyVisitItemSerializer(many=True)
    topPages = TopPageItemSerializer(many=True)
    countries = CountryItemSerializer(many=True)
    devices = DeviceItemSerializer(many=True)
