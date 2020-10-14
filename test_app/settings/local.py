from .base import *

INSTALLED_APPS += [
    'rest_framework',
    "rest_framework.authtoken",
    'django_sloop',
    'test_app.devices',
    'test_app.users',
]

DJANGO_SLOOP_SETTINGS = {
    "AWS_REGION_NAME": "",
    "AWS_ACCESS_KEY_ID": "",
    "AWS_SECRET_ACCESS_KEY": "",
    "SNS_IOS_APPLICATION_ARN": "test_ios_arn",
    "SNS_IOS_SANDBOX_APPLICATION_ARN": "test_ios_sandbox_arn",
    "SNS_ANDROID_APPLICATION_ARN": "test_android_arn",
    "DEFAULT_SOUND": "",
    "DEVICE_MODEL": "devices.Device",
    "LOG_SENT_MESSAGES": True,
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
