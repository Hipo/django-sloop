from rest_framework import serializers


class HelloSerializer(serializers.Serializer):
    """
    The serializer of the "Hello" end point
    """
    push_token = serializers.CharField(required=False)
    device_type = serializers.CharField(required=False)
    locale = serializers.CharField(required=False)
