from django.contrib.auth.models import User

from django_sloop.models import PushNotificationMixin

User.add_to_class("send_push_notification_async", PushNotificationMixin.send_push_notification_async)
User.add_to_class("get_active_pushable_device", PushNotificationMixin.get_active_pushable_device)
User.add_to_class("send_silent_push_notification_async", PushNotificationMixin.send_silent_push_notification_async)
User.add_to_class("get_badge_count", lambda x: 0)
