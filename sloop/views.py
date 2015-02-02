from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from sloop.serializers import HelloSerializer


class BaseHelloView(GenericAPIView):
    """
    An endpoint for retrieving Facebook access token and push token
    """
    serializer_class = HelloSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA)
        if serializer.is_valid():
            # Create push token object if necessary
            push_token, created = self.model.objects.get_or_create(
                token=serializer.data.get("push_token"),
                device_type=serializer.data.get("device_type"),
                defaults={
                    "profile": request.user,
                    "locale": serializer.data.get("locale"),
                }
            )
            if push_token.profile_id != request.user.id:
                push_token.profile = request.user
            push_token.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


