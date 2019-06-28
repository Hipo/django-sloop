![Sloop](/docs/img/splash.jpg?raw=true "Django-Sloop")


Django Sloop is the fastest & most reliable RESTful push notification service so far. This package contains some tools that will ease the implementation of sloop into django projects.

# Django-Sloop

## Installation

1. Install the package via Github or PIP (pip install django-sloop)

2. Add **django_sloop** to the INSTALLED_APPS list in the settings file.

3. Extend the django_sloop.models.AbstractSNSDevice class and create your own push token device model.

```python
# models.py

from django_sloop.models import AbstractSNSDevice


class Device(AbstractSNSDevice):
    pass
```

4. Run migrations.

5. Make sure that you fill necessary information at the settings file:

```python
# settings.py

DJANGO_SLOOP_SETTINGS = {
    "AWS_REGION_NAME": "",
    "AWS_ACCESS_KEY_ID": "",
    "AWS_SECRET_ACCESS_KEY": "",
    "SNS_IOS_APPLICATION_ARN": "test_ios_arn",
    "SNS_IOS_SANDBOX_ENABLED": False,
    "SNS_ANDROID_APPLICATION_ARN": "test_android_arn",
    "DEFAULT_SOUND": "",
    "DEVICE_MODEL": "users.Device",
}
```

6. Add django_sloop.models.PushNotificationMixin to your User model.

7. Add django_sloop.admin.SloopAdminMixin to your UserAdmin to enable sending push messages to users from Django admin panel.

```python
# admin.py

from django_sloop.admin import SloopAdminMixin
from django.contrib import admin

class UserAdmin(SloopAdminMixin, admin.ModelAdmin):
    pass
```

8. Add django rest framework urls to create and delete device.

```python
# urls.py
from django.conf.urls import url
from django.urls import include

urlpatterns = [
    # ...
    url(r'^api/devices/', include('django_sloop.urls')),
    # ...
]
```





Done!