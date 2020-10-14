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
    
    # (Optional) if you need to override Meta.
    class Meta(AbstractSNSDevice.Meta):
        pass
```

4. Add your Device model to django admin.

```python
from django_sloop.admin import DeviceAdmin
    
admin.site.register(Device, DeviceAdmin)
```

5. Make sure that you fill necessary information at the settings file:

```python
# settings.py

DJANGO_SLOOP_SETTINGS = {
    "AWS_REGION_NAME": "",
    "AWS_ACCESS_KEY_ID": "",
    "AWS_SECRET_ACCESS_KEY": "",
    "SNS_IOS_APPLICATION_ARN": "test_ios_arn",
    "SNS_IOS_SANDBOX_APPLICATION_ARN": "test_ios_sandbox_arn",
    "SNS_ANDROID_APPLICATION_ARN": "test_android_arn",
    "LOG_SENT_MESSAGES": False,  # False by default.
    "DEFAULT_SOUND": "",
    "DEVICE_MODEL": "module_name.Device",
}
```

You cannot change the DEVICE_MODEL setting during the lifetime of a project (i.e. once you have made and migrated models that depend on it) without serious effort. The model it refers to must be available in the first migration of
the app that it lives in.

6. Create migrations for newly created Device model and migrate.

**Note:** django_sloop's migrations must run after your Device is created. If you run into a problem while running migrations add following to the your migration file where the Device is created.
```
run_before = [
   ('django_sloop', '0001_initial'),
]
```

7. Add django_sloop.models.PushNotificationMixin to your User model.
```python
class User(PushNotificationMixin, ...):
    pass

user.send_push_notification_async(message="Sample push notification.")

```


8. Add django_sloop.admin.SloopAdminMixin to your UserAdmin to enable sending push messages to users from Django admin panel.

```python
# admin.py

from django_sloop.admin import SloopAdminMixin
from django.contrib import admin

class UserAdmin(SloopAdminMixin, admin.ModelAdmin):
    
    actions = ("send_push_notification", )
    
```

9. Add django rest framework urls to create and delete device.

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


## Mobile Client Integration

- Mobile clients should call the `create-or-update-device` endpoint in the following cases.
    1. First time you access the push token.
    2. If you already have push token you should send the same request to update last time the device is used. It's best to call this endpoint each time app is opened or come back from background. 

    Request: **POST /api/devices/**  
    Payload:
    ```
    {
        "push_token": "required string",
        "platform": "required ios or android",
        "model": "optional string",
        "locale": "optional string default to `en_US`",
    }
    ``` 

- Mobile clients should call the `delete-device` endpoint when user log outs.
    
    Request: **DELETE /api/devices/**  
    Payload:
    ```
    {
        "push_token": "required string",
    }
    ``` 


**Endpoint details will be available in the projects api documentation as well. There can be project level changes so please go to projects api documentation.**
