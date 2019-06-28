from django.apps import apps

from .settings import DJANGO_SLOOP_SETTINGS


def get_device_model():
    return apps.get_model(*DJANGO_SLOOP_SETTINGS["DEVICE_MODEL"].split("."))
