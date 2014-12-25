from django.db.models.loading import get_model
from django.conf import settings
from celery.task import task, periodic_task


@task()
def send_push_message(token_id, message, url, sound, extra):
    """
    Sends a push notification message to the specified tokens
    """
    # TODO: Put these line outside of the function to make it more optimized.
    push_token_class = get_model(*settings.SLOOP_DEVICE_TOKEN_MODEL.split("."))  # Monkey patchiiiing!

    device_push_token = push_token_class.objects.get(id=token_id)
    device_push_token.send_push_message(message, url, sound, extra)
    return "Message: %s" % message


# @periodic_task(run_every=timedelta(hours=3), name="clean_inactive_push_tokens")
# def clean_inactive_push_tokens():
#     """
#     Cleans inactive push tokens
#     """
#     airship = ua.Airship(settings.URBAN_AIRSHIP_APP_KEY, settings.URBAN_AIRSHIP_APP_MASTER_SECRET)
#     inactive_tokens = airship.feedback(datetime.now() - timedelta(days=1))
#     delete_tokens = []
#
#     for token, deactivation_date, alias in inactive_tokens:
#         delete_tokens.append(token)
#
#     if len(delete_tokens) == 0:
#         return "Didnt deleted any push tokens"
#
#     from moment.profiles.models import DevicePushToken
#     DevicePushToken.objects.filter(token__in=delete_tokens).delete()
#     return "Deleted push tokens %s" % str(delete_tokens)
