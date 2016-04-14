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
        try:
            data = self.request.data
        except AttributeError:
            data = self.request.DATA
        return data

    def get_token(self):
        """
        To support both DRF 2 and 3
        """
        data = self.get_request_data()
        key = 'push_token'
        from_url = self.kwargs.get(key)
        from_body = data.get(key)
        return from_url or from_body

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.get_request_data())
        if serializer.is_valid():
            # Create push token object if necessary
            push_token, created = self.get_queryset().get_or_create(
                token=serializer.data.get("push_token"),
                device_type=serializer.data.get("device_type"),
                defaults={
                    "profile": request.user,
                    "locale": serializer.data.get("locale"),
                    "device_model": serializer.data.get("device_model")
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
        return self.get_queryset(token=self.get_token(), profile_id=self.request.user.id)
