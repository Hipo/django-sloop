from django.db.models.loading import get_model
from django.conf import settings
from celery.task import task


concrete_device_model = get_model(*settings.SLOOP_DEVICE_TOKEN_MODEL.split("."))  # Monkey patchiiiing!


@task()
def send_push_message(token_id, message, url, sound, extra):
    """
    Sends a push notification message to the specified tokens
    """
    device = concrete_device_model.objects.get(id=token_id)
    device.send_push_message(message, url, sound, extra)
    return "Message: %s" % message
