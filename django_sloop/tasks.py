from celery import shared_task

from .utils import get_device_model


@shared_task()
def send_push_notification(device_id, message, url, badge_count, sound, extra, category, **kwargs):
    """
    Sends a push notification message to the specified tokens
    """
    device_model = get_device_model()
    device = device_model.objects.get(id=device_id)
    device.send_push_notification(message, url, badge_count, sound, extra, category, **kwargs)
    return "Message: %s" % message


@shared_task()
def send_silent_push_notification(device_id, extra, badge_count, content_available, **kwargs):
    """
    Sends a push notification message to the specified tokens
    """
    device_model = get_device_model()
    device = device_model.objects.get(id=device_id)
    device.send_silent_push_notification(extra, badge_count, content_available, **kwargs)
    return "Silent push"
