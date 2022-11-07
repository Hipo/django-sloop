from django.urls import path
from .views import CreateDeleteDeviceView

app_name = 'django_sloop'

urlpatterns = (
    path('', CreateDeleteDeviceView.as_view(), name="create-delete-device"),
)
