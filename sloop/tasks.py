from django.db.models.loading import get_model
from django.conf import settings
from celery.task import task


concrete_device_model = get_model(*settings.SLOOP_DEVICE_TOKEN_MODEL.split("."))


@task()
def send_push_notification(token_id, message, url, sound, extra, category):
    """
    Sends a push notification message to the specified tokens
    """
    device = concrete_device_model.objects.get(id=token_id)
    device.send_push_notification(message, url, sound, extra, category)
    return "Message: %s" % message

@task()
def send_silent_push_notification(token_id, extra, content_available):
    """
    Sends a push notification message to the specified tokens
    """
    device = concrete_device_model.objects.get(id=token_id)
    device.send_silent_push_notification(extra, content_available)
    return "Silent push"
