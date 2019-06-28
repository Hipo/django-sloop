from django.conf.urls import url
from .views import CreateDeleteDeviceView

app_name = 'django_sloop'

urlpatterns = (
    url(r'^$', CreateDeleteDeviceView.as_view(), name="create-delete-device"),
)
