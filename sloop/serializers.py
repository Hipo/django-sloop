from rest_framework import serializers


class DeviceSerializer(serializers.Serializer):
    """
    The serializer of the "Hello" end point
    """
    push_token = serializers.CharField(required=True)
    device_type = serializers.CharField(required=False)
    device_model = serializers.CharField(required=False)
    locale = serializers.CharField(required=False)
