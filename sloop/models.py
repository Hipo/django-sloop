import json
import requests
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_unicode
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _, activate, get_language, gettext
from django.template.defaultfilters import truncatechars

from sloop.constants import *
from sloop.tasks import send_push_notification, send_silent_push_notification


class PushNotificationMixin(object):
    """
    A Mixin that handles push notification sending through the UserProfile model.
    """
    @property
    def active_push_token(self):
        """
        Finds and returns the last active push token for this user, if available
        """
        try:
            push_token = self.push_tokens.latest()
        except ObjectDoesNotExist:
            return None
        return push_token

    def send_push_message(self, *args, **kwargs):
        return self.send_push_notification(*args, **kwargs)

    def send_push_notification(self, message, url=None, sound=None, extra=None, category=None):
        """
        Sends a push notification to the user's last active device
        """
        # Print message to console if this is a development environment.
        if settings.DEBUG:
            print "Push notification: %s / Receiver: %s" % (message, self)

        token = self.active_push_token
        if not token:
            return False

        message = token.translate_message(message, current_language=get_language())
        send_push_notification.delay(
            token.id,
            message,
            url,
            sound,
            extra,
            category
        )
        return True

    def send_silent_push_notification(self, extra=None, content_available=True):
        """
        Sends a push notification to the user's last active device
        """
        # Print message to console if this is a development environment.
        if settings.DEBUG:
            print "Silent push notification to: %s" % self

        token = self.active_push_token
        if not token:
            return False

        send_silent_push_notification.delay(
            token.id,
            extra,
            content_available
        )
        return True


class DeviceBaseClass(models.Model):
    """
    A push token for a device associated with a user profile
    """
    profile = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="push_tokens", verbose_name=_("Profile"))
    locale = models.CharField(_("locale"), max_length=255, default="en_US")
    token = models.CharField(_("Token"), max_length=255)
    date_updated = models.DateTimeField(_("Date Updated"), auto_now=True)
    device_type = models.CharField(
        _("Device Type"),
        max_length=255,
        blank=True,
        choices=DEVICE_PUSH_TOKEN_TYPES,
        default=DEVICE_PUSH_TOKEN_TYPE_IOS
    )

    class Meta:
        verbose_name = _("Device Push Token")
        verbose_name_plural = _("Device Push Tokens")
        unique_together = ("token", "device_type")
        ordering = ("-date_updated",)
        get_latest_by = "date_updated"
        abstract = True

    def __unicode__(self):
        return smart_unicode(_("Push Token %(token)s for %(profile)s") % {
            "profile": self.profile.full_name,
            "token": self.token,
        })

    def get_badge_count(self):
        """
        A placeholder for the badge count calculations
        """
        return 0

    def get_extra_data(self, extra_data):
        """
        A placeholder for the extra push data.
        """
        return extra_data

    def prepare_message(self, message):
        """
        Prepares message before sending.
        """
        return truncatechars(message, 255)

    def process_sloop_response(self, data):
        """
        Process the message coming from sloop
        """
        pass

    def get_server_call_url(self):
        """
        Generates the url for the server call
        """
        sloop_server_domain = SLOOP_SERVER_DOMAIN
        sloop_device_token_path_template = SLOOP_DEVICE_TOKEN_PATH_TEMPLATE
        url = sloop_server_domain + sloop_device_token_path_template % settings.SLOOP_APP_KEY
        url = url + "?" + urlencode({
            "token": settings.SLOOP_APP_TOKEN
        })
        return url

    def send_push_notification(self, message, url, sound, extra, category, *args, **kwargs):
        """
        Sends push message using device token
        """
        extra_data = self.get_extra_data(extra)
        if url:
            extra_data["url"] = url

        data = {
            'device_token': self.token,
            'device_type': self.device_type,
            'alert': self.prepare_message(message),
            'sound': sound,
            'custom': extra_data,
            'badge': self.get_badge_count(),
            'category': category
        }
        data.update(kwargs)
        self._send_payload(data)
        return True

    def send_silent_push_notification(self, extra, content_available, *args, **kwargs):
        extra_data = self.get_extra_data(extra)

        data = {
            'device_token': self.token,
            'device_type': self.device_type,
            'content-available': content_available,
            'sound': '',
            'badge': self.get_badge_count(),
            'custom': extra_data
        }
        data.update(kwargs)
        self._send_payload(data)
        return True

    def _send_payload(self, data):
        headers = {'content-type': 'application/json'}
        r = requests.post(self.get_server_call_url(), data=json.dumps(data), headers=headers)
        r.raise_for_status()
        self.process_sloop_response(r.json())

    def translate_message(self, message, current_language):
        token_language_code = self.locale[:2] if self.locale else "en"
        try:
            activate(token_language_code)
            message = gettext(message)
        finally:
            activate(current_language)

        return message