import json
import time
from random import randint
from unittest import skipIf

from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from mock import Mock

from django_sloop.utils import get_device_model
from .handlers import SNSHandler
from .settings import DJANGO_SLOOP_SETTINGS

User = get_user_model()

TEST_SNS_ENDPOINT_ARN = "test_sns_endpoint_arn"
TEST_IOS_PUSH_TOKEN = "test_ios_push_token"
TEST_ANDROID_PUSH_TOKEN = "test_android_push_token"


Device = get_device_model()


class SNSHandlerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('username', "username@test.com", "test123")
        self.ios_device = Device.objects.create(user=self.user, push_token=TEST_IOS_PUSH_TOKEN, platform=Device.PLATFORM_IOS)
        self.android_device = Device.objects.create(user=self.user, push_token=TEST_ANDROID_PUSH_TOKEN, platform=Device.PLATFORM_ANDROID)

    def test_get_ios_application_arn(self):
        sns_client = Mock()
        SNSHandler.client = sns_client
        handler = SNSHandler(self.ios_device)
        self.assertEqual(handler.application_arn, DJANGO_SLOOP_SETTINGS["SNS_IOS_APPLICATION_ARN"])

    def test_get_android_application_arn(self):
        sns_client = Mock()
        SNSHandler.client = sns_client
        handler = SNSHandler(self.android_device)
        self.assertEqual(handler.application_arn, DJANGO_SLOOP_SETTINGS["SNS_ANDROID_APPLICATION_ARN"])

    def test_create_platform_endpoint(self):
        sns_client = Mock()
        sns_client.create_platform_endpoint.return_value = {
            'EndpointArn': TEST_SNS_ENDPOINT_ARN
        }
        sns_client.publish.return_value = ""
        SNSHandler.client = sns_client
        handler = SNSHandler(self.ios_device)
        self.assertEqual(handler.get_or_create_platform_endpoint_arn(), TEST_SNS_ENDPOINT_ARN)

        sns_client.create_platform_endpoint.assert_called_once_with(
            PlatformApplicationArn=DJANGO_SLOOP_SETTINGS["SNS_IOS_APPLICATION_ARN"],
            Token=self.ios_device.push_token,
        )

        self.assertEqual(self.ios_device.sns_platform_endpoint_arn, TEST_SNS_ENDPOINT_ARN)

    def test_get_platform_endpoint(self):
        sns_client = Mock()
        sns_client.create_platform_endpoint.return_value = {
            'EndpointArn': TEST_SNS_ENDPOINT_ARN
        }
        SNSHandler.client = sns_client
        self.ios_device.sns_platform_endpoint_arn = "test_arn"
        self.ios_device.save()
        handler = SNSHandler(self.ios_device)
        self.assertEqual(handler.get_or_create_platform_endpoint_arn(), "test_arn")

        # create_platform_endpoint() is not called.
        self.assertFalse(sns_client.create_platform_endpoint.called)


class DeviceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("username", "username@test.com", "test123")
        self.ios_device = Device.objects.create(user=self.user, push_token=TEST_IOS_PUSH_TOKEN, platform=Device.PLATFORM_IOS)
        self.android_device = Device.objects.create(user=self.user, push_token=TEST_ANDROID_PUSH_TOKEN, platform=Device.PLATFORM_ANDROID)

    def test_send_ios_push_notification(self):
        sns_client = Mock()
        sns_test_message_id = "test_message_" + str(randint(0, 9999))
        sns_client.publish.return_value = {
            "MessageId": sns_test_message_id
        }
        SNSHandler.client = sns_client

        self.ios_device.sns_platform_endpoint_arn = "test_ios_arn"
        self.ios_device.save()

        self.ios_device.send_push_notification(message="test_message", url="test_url", badge_count=3, sound="test_sound", extra={"foo": "bar"}, category="test_category", foo="bar")

        sns_client.publish.assert_called_once()
        call_args, call_kwargs = sns_client.publish.call_args_list[0]
        self.assertEqual(call_kwargs["TargetArn"], self.ios_device.sns_platform_endpoint_arn)
        self.assertEqual(call_kwargs["MessageStructure"], "json")
        expected_message = {
            'APNS': {
                'aps': {
                    'alert': "test_message",
                    'sound': 'test_sound',
                    'badge': 3,
                    'category': "test_category",
                    'custom': {"foo": "bar", "url": "test_url"},
                    'foo': 'bar'
                }
            }
        }

        actual_message = json.loads(call_kwargs["Message"])
        actual_message["APNS"] = json.loads(actual_message["APNS"])

        self.assertDictEqual(expected_message, actual_message)

        push_message = self.ios_device.push_messages.get()
        self.assertEqual(push_message.sns_message_id, sns_test_message_id)
        self.assertEqual(push_message.sns_response, json.dumps({
            "MessageId": sns_test_message_id
        }))

    def test_send_android_push_notification(self):
        sns_client = Mock()
        sns_test_message_id = "test_message_" + str(randint(0, 9999))
        sns_client.publish.return_value = {
            "MessageId": sns_test_message_id
        }
        SNSHandler.client = sns_client

        self.android_device.sns_platform_endpoint_arn = "test_android_arn"
        self.android_device.save()

        self.android_device.send_push_notification(message="test_message", url="test_url", badge_count=3, sound="test_sound", extra={"foo": "bar"}, category="test_category", foo="bar")

        sns_client.publish.assert_called_once()
        call_args, call_kwargs = sns_client.publish.call_args_list[0]
        self.assertEqual(call_kwargs["TargetArn"], self.android_device.sns_platform_endpoint_arn)
        self.assertEqual(call_kwargs["MessageStructure"], "json")
        expected_message = {
            'GCM': {
                'data': {
                    'alert': "test_message",
                    'sound': 'test_sound',
                    'badge': 3,
                    'category': "test_category",
                    'custom': {"foo": "bar", "url": "test_url"},
                    'foo': 'bar'
                }
            }
        }

        actual_message = json.loads(call_kwargs["Message"])
        actual_message["GCM"] = json.loads(actual_message["GCM"])

        self.assertDictEqual(expected_message, actual_message)

        push_message = self.android_device.push_messages.get()
        self.assertEqual(push_message.sns_message_id, sns_test_message_id)
        self.assertEqual(push_message.sns_response, json.dumps({
            "MessageId": sns_test_message_id
        }))

    def test_send_ios_silent_push_notification(self):
        sns_client = Mock()
        sns_test_message_id = "test_message_" + str(randint(0, 9999))
        sns_client.publish.return_value = {
            "MessageId": sns_test_message_id
        }
        SNSHandler.client = sns_client

        self.ios_device.sns_platform_endpoint_arn = "test_ios_arn"
        self.ios_device.save()

        self.ios_device.send_silent_push_notification(badge_count=0, extra={"foo": "bar"}, content_available=True, foo="bar")

        sns_client.publish.assert_called_once()
        call_args, call_kwargs = sns_client.publish.call_args_list[0]
        self.assertEqual(call_kwargs["TargetArn"], self.ios_device.sns_platform_endpoint_arn)
        self.assertEqual(call_kwargs["MessageStructure"], "json")
        expected_message = {
            'APNS': {
                'aps': {
                    'content-available': True,
                    'sound': '',
                    'badge': 0,
                    'custom': {"foo": "bar"},
                    'foo': 'bar'
                }
            }
        }

        actual_message = json.loads(call_kwargs["Message"])
        actual_message["APNS"] = json.loads(actual_message["APNS"])

        self.assertDictEqual(expected_message, actual_message)

        push_message = self.ios_device.push_messages.get()
        self.assertEqual(push_message.sns_message_id, sns_test_message_id)
        self.assertEqual(push_message.sns_response, json.dumps({
            "MessageId": sns_test_message_id
        }))

    def test_send_android_silent_push_notification(self):
        sns_client = Mock()
        sns_test_message_id = "test_message_" + str(randint(0, 9999))
        sns_client.publish.return_value = {
            "MessageId": sns_test_message_id
        }
        SNSHandler.client = sns_client

        self.android_device.sns_platform_endpoint_arn = "test_android_arn"
        self.android_device.save()

        self.android_device.send_silent_push_notification(badge_count=0, extra={"foo": "bar"}, content_available=True, foo="bar")

        sns_client.publish.assert_called_once()
        call_args, call_kwargs = sns_client.publish.call_args_list[0]
        self.assertEqual(call_kwargs["TargetArn"], self.android_device.sns_platform_endpoint_arn)
        self.assertEqual(call_kwargs["MessageStructure"], "json")
        expected_message = {
            'GCM': {
                'data': {
                    'content-available': True,
                    'sound': '',
                    'badge': 0,
                    'custom': {"foo": "bar"},
                    'foo': 'bar'
                }
            }
        }

        actual_message = json.loads(call_kwargs["Message"])
        actual_message["GCM"] = json.loads(actual_message["GCM"])

        self.assertDictEqual(expected_message, actual_message)

        push_message = self.android_device.push_messages.get()
        self.assertEqual(push_message.sns_message_id, sns_test_message_id)
        self.assertEqual(push_message.sns_response, json.dumps({
            "MessageId": sns_test_message_id
        }))

    def test_invalidate_device_if_push_message_fails(self):
        sns_client = Mock()
        SNSHandler.client = sns_client
        sns_client.publish.side_effect = ClientError(error_response={
            "Error": {
                "Code": "EndpointDisabled"
            }
        }, operation_name="test")

        self.ios_device.sns_platform_endpoint_arn = "test_ios_arn"
        self.ios_device.save()

        self.ios_device.send_push_notification(message="test")

        # Device must be deleted.
        self.ios_device.refresh_from_db()
        self.assertIsNotNone(self.ios_device.deleted_at)

        push_message = self.ios_device.push_messages.get()
        self.assertIsNone(push_message.sns_message_id)
        self.assertEqual(push_message.sns_response, json.dumps({
            "Error": {
                "Code": "EndpointDisabled"
            }
        }))


@skipIf('rest_framework.authtoken' not in settings.INSTALLED_APPS, "rest_framework.authtoken is not in installed apps.")
class DeviceAPITests(TestCase):

    def setUp(self):
        from rest_framework.authtoken.models import Token
        from rest_framework.test import APIClient
        from rest_framework import status
        self.Token = Token
        self.APIClient = APIClient
        self.status = status

        self.client, self.user = self.create_test_user_client()
        self.ios_device = Device.objects.create(user=self.user, push_token=TEST_IOS_PUSH_TOKEN, platform=Device.PLATFORM_IOS)
        self.android_device = Device.objects.create(user=self.user, push_token=TEST_ANDROID_PUSH_TOKEN, platform=Device.PLATFORM_ANDROID)
        self.create_delete_url = reverse("django_sloop:create-delete-device")

    def create_test_user_client(self, **user_data):
        millis = int(round(time.time() * 1000))
        user = User.objects.create_user("username" + str(millis), "username@test.com", "test123")
        token, _ = self.Token.objects.get_or_create(user=user)
        client = self.APIClient()
        client.default_format = 'json'
        client.force_authenticate(user=user, token=token.key)

        return client, user

    def test_api_create_device(self):
        from .serializers import DeviceSerializer

        data = {
            "push_token": "test_ios_push_token2",
            "platform": Device.PLATFORM_IOS
        }
        response = self.client.post(self.create_delete_url, data=data)
        self.assertEqual(response.status_code, self.status.HTTP_201_CREATED)
        device = self.user.devices.get(**data)
        self.assertEqual(response.data, DeviceSerializer(device).data)

    def test_api_delete_device(self):
        non_device_owner_client, non_device_owner = self.create_test_user_client()

        data = {
            "push_token": self.ios_device.push_token
        }
        response = non_device_owner_client.delete(self.create_delete_url, data=data)
        self.assertEqual(response.status_code, self.status.HTTP_404_NOT_FOUND)

        response = self.client.delete(self.create_delete_url, data=data)

        self.assertEqual(response.status_code, self.status.HTTP_204_NO_CONTENT)
        self.ios_device.refresh_from_db()
        self.assertIsNotNone(self.ios_device.deleted_at)
