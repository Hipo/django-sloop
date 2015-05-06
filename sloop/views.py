from rest_framework.generics import CreateAPIView, get_object_or_404
from rest_framework.mixins import DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from sloop.serializers import DeviceSerializer


class BaseDeviceView(CreateAPIView, DestroyModelMixin):
    """
    An endpoint for creating / deleting devices.
    If you are customizing DeviceBaseClass, you should use your own views.
    """
    serializer_class = DeviceSerializer
    permission_classes = (IsAuthenticated,)

    def get_request_data(self):
        """
        To support both DRF 2 and 3
        """
        try:
            return self.request.data
        except AttributeError:
            return self.request.DATA

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.get_request_data())
        if serializer.is_valid():
            # Create push token object if necessary
            push_token, created = self.get_queryset().get_or_create(
                token=serializer.data.get("push_token"),
                device_type=serializer.data.get("device_type"),
                device_model=serializer.data.get("device_model"),
                defaults={
                    "profile": request.user,
                    "locale": serializer.data.get("locale"),
                }
            )
            if push_token.profile_id != request.user.id:
                push_token.profile = request.user
            push_token.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def get_object(self):
        """
        Override get_object for delete endpoint
        """
        return get_object_or_404(self.get_queryset(), token=self.get_request_data().get('push_token'))