from rest_framework import serializers

# PUT
class ClockinSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    start = serializers.DateTimeField(required=False)
    status = serializers.IntegerField(default=0)
    location_geo = serializers.CharField(required=False)
    location_id = serializers.IntegerField(required=False)

class ClockoutSerializer(serializers.Serializer):
    end = serializers.DateTimeField(required=False)
    ID = serializers.CharField()
    location_geo = serializers.CharField(required=False)
    site_name = serializers.CharField(required=False)

class WriteupSerializer(serializers.Serializer):
#    signature = serializers.FileField()
    password = serializers.CharField()

class ValidateSerializer(serializers.Serializer):
    ID = serializers.CharField()
    week = serializers.CharField(required=False)
    unvalidate = serializers.BooleanField(default=False)

class FenceSerializer(serializers.Serializer):
    location_id = serializers.IntegerField()
    location_geo = serializers.CharField()

class MessageSerializer(serializers.Serializer):
    location_geo = serializers.CharField(required=False)
    location_id = serializers.IntegerField(required=False)
    text = serializers.CharField()

# RESPONSES
class SetupSerializer(serializers.Serializer):
    geo_frecuency = serializers.IntegerField()
    desired_accuracy = serializers.IntegerField()
    stationary_radius = serializers.IntegerField()
    distance_filter = serializers.IntegerField()
    location_timeout = serializers.IntegerField()
    IOS_config = serializers.IntegerField()
    rest_reminder = serializers.IntegerField()
    full_name = serializers.CharField()

class ClockedinSerializer(serializers.Serializer):
    start = serializers.DateTimeField()

class SiteinfoSerializer(serializers.Serializer):
    location_id = serializers.IntegerField(required=False)
    site_name = serializers.CharField()

class StatusSerializer(serializers.Serializer):
    status = serializers.IntegerField()
    data = serializers.CharField(required=False)
    site_name = serializers.CharField(required=False)

class HistentrySerializer(serializers.Serializer):
    ID = serializers.CharField()
    week = serializers.CharField(required=False)
    status = serializers.IntegerField(required=False)
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    site_name = serializers.CharField(required=False)

class HistorySerializer(serializers.Serializer):
    status = serializers.IntegerField()
    offset = serializers.IntegerField(required=False)
    entries = HistentrySerializer(many = True)

class WithinSerializer(serializers.Serializer):
    within = serializers.IntegerField()
    notification = serializers.CharField(required=False)

# ALERT
class AlertSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    entry_id = serializers.IntegerField(required=False)
    location_geo = serializers.CharField(required=False)
    type = serializers.IntegerField()
    text = serializers.CharField()
    time = serializers.DateTimeField()
