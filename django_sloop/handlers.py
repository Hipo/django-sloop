import json

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

from .settings import DJANGO_SLOOP_SETTINGS

from .models import AbstractSNSDevice


class SNSHandler(object):

    client = None

    def __init__(self, device):
        self.device = device
        self.client = self.get_client()

    def get_client(self):
        if self.client:
            return self.client

        client = boto3.client(
            'sns',
            region_name=DJANGO_SLOOP_SETTINGS.get("AWS_REGION_NAME") or None,
            aws_access_key_id=DJANGO_SLOOP_SETTINGS.get("AWS_ACCESS_KEY_ID") or None,
            aws_secret_access_key=DJANGO_SLOOP_SETTINGS.get("AWS_SECRET_ACCESS_KEY") or None
        )

        return client

    @property
    def application_arn(self):
        if self.device.platform == AbstractSNSDevice.PLATFORM_IOS:
            application_arn = DJANGO_SLOOP_SETTINGS.get("SNS_IOS_APPLICATION_ARN")
        elif self.device.platform == AbstractSNSDevice.PLATFORM_ANDROID:
            application_arn = DJANGO_SLOOP_SETTINGS.get("SNS_ANDROID_APPLICATION_ARN")
        else:
            assert False

        return application_arn

    def send_push_notification(self, message, url, badge_count, sound, extra, category, **kwargs):

        if self.device.platform == AbstractSNSDevice.PLATFORM_IOS:
            data = self.generate_apns_push_notification_message(message, url, badge_count, sound, extra, category, **kwargs)
        else:
            data = self.generate_gcm_push_notification_message(message, url, badge_count, sound, extra, category, **kwargs)

        return self._send_payload(data)

    def send_silent_push_notification(self, extra, badge_count, content_available, **kwargs):

        if self.device.platform == AbstractSNSDevice.PLATFORM_IOS:
            data = self.generate_apns_silent_push_notification_message(extra, badge_count, content_available, **kwargs)
        else:
            data = self.generate_gcm_silent_push_notification_message(extra, badge_count, content_available, **kwargs)

        return self._send_payload(data)

    def generate_gcm_push_notification_message(self, message, url, badge_count, sound, extra, category, **kwargs):
        if not extra:
            extra = {}

        if url:
            extra["url"] = url

        data = {
            'alert': message,
            'sound': sound,
            'custom': extra,
            'badge': badge_count,
            'category': category
        }
        data.update(kwargs)

        data_bundle = {
            'data': data
        }

        data_string = json.dumps(data_bundle, ensure_ascii=False)

        return {
            'GCM': data_string
        }

    def generate_gcm_silent_push_notification_message(self, extra, badge_count, content_available, **kwargs):
        data = {
            'content-available': content_available,
            'sound': '',
            'badge': badge_count,
            'custom': extra
        }
        data.update(kwargs)

        data_bundle = {
            'data': data
        }

        data_string = json.dumps(data_bundle, ensure_ascii=False)

        return {
            'GCM': data_string
        }

    def generate_apns_push_notification_message(self, message, url, badge_count, sound, extra, category, **kwargs):
        if not extra:
            extra = {}

        if url:
            extra["url"] = url

        data = {
            'alert': message,
            'sound': sound,
            'custom': extra,
            'badge': badge_count,
            'category': category
        }
        data.update(kwargs)

        apns_bundle = {
            'aps': data
        }
        apns_string = json.dumps(apns_bundle, ensure_ascii=False)

        if DJANGO_SLOOP_SETTINGS.get("SNS_IOS_SANDBOX_ENABLED"):
            return {
                'APNS_SANDBOX': apns_string
            }
        else:
            return {
                'APNS': apns_string
            }

    def generate_apns_silent_push_notification_message(self, extra, badge_count, content_available, **kwargs):

        data = {
            'content-available': content_available,
            'sound': '',
            'badge': badge_count,
            'custom': extra
        }
        data.update(kwargs)

        apns_bundle = {
            'aps': data
        }
        apns_string = json.dumps(apns_bundle, ensure_ascii=False)

        if DJANGO_SLOOP_SETTINGS.get("SNS_IOS_SANDBOX_ENABLED"):
            return {
                'APNS_SANDBOX': apns_string
            }
        else:
            return {
                'APNS': apns_string
            }

    def get_or_create_platform_endpoint_arn(self):
        if self.device.sns_platform_endpoint_arn:
            endpoint_arn = self.device.sns_platform_endpoint_arn
        else:
            endpoint_response = self.client.create_platform_endpoint(
                PlatformApplicationArn=self.application_arn,
                Token=self.device.push_token,
            )
            endpoint_arn = endpoint_response['EndpointArn']
            self.device.sns_platform_endpoint_arn = endpoint_arn
            self.device.save(update_fields=["sns_platform_endpoint_arn"])

        return endpoint_arn

    def _send_payload(self, data):
        endpoint_arn = self.get_or_create_platform_endpoint_arn()
        message = json.dumps(data, ensure_ascii=False)

        if settings.DEBUG:
            print("ARN:" + endpoint_arn)
            print(message)

        try:
            publish_result = self.client.publish(
                TargetArn=endpoint_arn,
                Message=message,
                MessageStructure='json'
            )
        except ClientError as exc:
            if exc.response['Error']["Code"] == "EndpointDisabled":
                # Push token is not valid anymore.
                # App deleted or push notifications are turned off by the user.
                self.device.invalidate()
            else:
                raise

            return message, exc.response

        if settings.DEBUG:
            print(publish_result)
        return message, publish_result
