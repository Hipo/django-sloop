from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import truncatechars

from .settings import DJANGO_SLOOP_SETTINGS
from . import tasks


class PushNotificationMixin(object):
    """
    A Mixin that handles push notification sending through the User model.
    """

    def get_badge_count(self):
        return 0

    def get_active_pushable_device(self):
        """
        Finds and returns the last active device with push token for this user, if available
        """
        try:
            device = self.devices.latest()
        except ObjectDoesNotExist:
            return None
        return device

    def send_push_notification_async(self, message, url=None, sound=None, extra=None, category=None, **kwargs):
        device = self.get_active_pushable_device()
        if not device:
            return False

        # Print message to console if this is a development environment.
        if settings.DEBUG:
            print("Push notification: %s / Receiver: %s" % (message, self))

        sound = sound or DJANGO_SLOOP_SETTINGS.get("DEFAULT_SOUND") or None

        tasks.send_push_notification.delay(
            device.id,
            message,
            url,
            self.get_badge_count(),
            sound,
            extra,
            category,
            **kwargs
        )

    def send_silent_push_notification_async(self, extra=None, content_available=True, **kwargs):
        """
        Sends a push notification to the user's last active device
        """
        # Print message to console if this is a development environment.
        if settings.DEBUG:
            print("Silent push notification to: %s" % self)

        device = self.get_active_pushable_device()
        if not device:
            return False

        tasks.send_silent_push_notification.delay(
            device.id,
            extra,
            self.get_badge_count(),
            content_available,
            **kwargs
        )


class AbstractSNSDevice(models.Model):

    PLATFORM_IOS = "ios"
    PLATFORM_ANDROID = "android"

    PLATFORM_CHOICES = (
        (PLATFORM_IOS, "iOS"),
        (PLATFORM_ANDROID, "Android"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="devices", on_delete=models.CASCADE)
    locale = models.CharField(max_length=255, default="en_US")
    push_token = models.CharField(max_length=255, null=True)
    platform = models.CharField(max_length=255, choices=PLATFORM_CHOICES)
    model = models.CharField(max_length=255, blank=True)
    sns_platform_endpoint_arn = models.CharField(_("SNS Platform Endpoint"), max_length=255, null=True, unique=True)

    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")
        unique_together = ("push_token", "platform")
        ordering = ("-date_updated",)
        get_latest_by = "date_updated"
        abstract = True

    def __str__(self):
        return smart_text(_("Push Token %(push_token)s for %(user)s") % {
            "profile": self.user.full_name,
            "push_token": self.push_token,
        })

    def invalidate(self):
        self.delete()

    def prepare_message(self, message):
        """
        Prepares message before sending.
        """
        return truncatechars(message, 255)

    def send_push_notification(self, message, url=None, badge_count=None, sound=None, extra=None, category=None, **kwargs):
        """
        Sends push message using device push token
        """
        from .handlers import SNSHandler

        message = self.prepare_message(message)

        handler = SNSHandler(device=self)
        response = handler.send_push_notification(message, url, badge_count, sound, extra, category, **kwargs)
        return response

    def send_silent_push_notification(self, extra=None, badge_count=None, content_available=None, **kwargs):
        """
        Sends silent push notification
        """
        from .handlers import SNSHandler
        handler = SNSHandler(device=self)
        response = handler.send_silent_push_notification(extra, badge_count, content_available, **kwargs)
        return response
