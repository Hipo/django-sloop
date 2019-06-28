from rest_framework.generics import CreateAPIView, get_object_or_404
from rest_framework.mixins import DestroyModelMixin
from rest_framework.permissions import IsAuthenticated

from .utils import get_device_model
from .serializers import DeviceSerializer


class CreateDeleteDeviceView(CreateAPIView, DestroyModelMixin):
    """
    An endpoint for creating & deleting devices.
    """
    serializer_class = DeviceSerializer
    permission_classes = (IsAuthenticated,)

    def perform_destroy(self, instance):
        instance.invalidate()

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def get_object(self):
        """
        Override get_object for delete endpoint
        """
        device_model = get_device_model()
        return get_object_or_404(device_model._default_manager, push_token=self.request.data.get('push_token'), user=self.request.user)
