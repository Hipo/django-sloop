import json
import requests
from django.conf import settings
from django.utils.http import urlencode


def send_push_message_using_device_token(push_token, message, device_type, badge_count=0, sound="default", extra=None, *args, **kwargs):
    """
    Sends push message using device token
    """
    SLOOP_SERVER_DOMAIN = "http://pushserver.hipo.biz:8193"
    SLOOP_NOTIFICATION_BY_DEVICE_TOKEN_PATH_TEMPLATE = "/application/%s/device/notify"

    data = {
        'device_token': push_token,
        'device_type': device_type,
        'alert': message,
        'sound': sound,
        'badge': badge_count,
        'custom': extra or dict(),
    }
    horn_notify_url = SLOOP_SERVER_DOMAIN + SLOOP_NOTIFICATION_BY_DEVICE_TOKEN_PATH_TEMPLATE % settings.SLOOP_APP_KEY
    horn_notify_url = horn_notify_url + "?" + urlencode({
        "token": settings.SLOOP_APP_TOKEN
    })

    r = requests.post(horn_notify_url, data=json.dumps(data))
    r.raise_for_status()
    return r.status_code == requests.codes.ok