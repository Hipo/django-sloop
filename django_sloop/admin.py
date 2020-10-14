from django.conf.urls import url
from django.contrib import admin
from django.contrib import messages
from django.urls import reverse
from django.utils.http import urlencode
from django.views.generic import FormView
from django.template.response import TemplateResponse
from django import forms

import json

from django_sloop.handlers import SNSHandler
from django_sloop.models import PushMessage
from django.utils.translation import ugettext_lazy as _


class PushNotificationForm(forms.Form):

    message = forms.CharField(max_length=255, label='Message:')
    extra = forms.CharField(max_length=255, widget=forms.Textarea, required=False, initial=json.dumps(dict()), label='Extra data as JSON:')
    url = forms.CharField(max_length=255, required=False, label='URL:')
    receivers = forms.CharField(widget=forms.HiddenInput)

    def clean(self):
        try:
            self.cleaned_data['extra'] = json.loads(self.cleaned_data['extra'])
            if self.cleaned_data['url']:
                self.cleaned_data['extra']["url"] = self.cleaned_data['url']
            self.cleaned_data['receivers'] = json.loads(self.cleaned_data['receivers'])
        except (TypeError, ValueError) as ex:
            self.add_error('extra', ex.message)
        except KeyError:
            self.add_error(None, 'Could not retrieve push notification receivers, please try again.')

        return self.cleaned_data


class PushNotificationView(FormView):

    template_name = 'django_sloop/push_notification.html'
    form_class = PushNotificationForm

    def form_valid(self, form):
        self.receivers = form.cleaned_data['receivers']
        model_admin = self.kwargs.get('model_admin')
        receiver_ids = model_admin.get_receivers_queryset(self.receivers)
        for receiver_id in receiver_ids:
            user = model_admin.model.objects.get(pk=receiver_id)
            user.send_push_notification_async(form.cleaned_data['message'], extra=form.cleaned_data['extra'])

        return super(PushNotificationView, self).form_valid(form)

    def get_initial(self):
        initial = super(PushNotificationView, self).get_initial()
        if not initial.get("receivers") and self.request.GET.get("receivers"):
            initial["receivers"] = json.loads(self.request.GET.get("receivers"))
        return initial

    def get_success_url(self):
        messages.info(self.request, "Push notification has been sent.")
        model_admin = self.kwargs.get('model_admin')
        url = reverse('admin:%s_%s_send_push_notification' % (model_admin.model._meta.app_label, model_admin.model._meta.model_name))
        url += "?" + urlencode({
            'receivers': json.dumps(self.receivers)
        })
        return url

    def get_context_data(self, **kwargs):
        context = super(PushNotificationView, self).get_context_data(**kwargs)
        model_admin = self.kwargs.get('model_admin')
        admin_site = model_admin.admin_site
        opts = model_admin.model._meta

        context.update({
            'admin_site': admin_site.name,
            'title': 'Send Push Notification',
            'opts': opts,
            'app_label': opts.app_label,
            'view_url': reverse('admin:%s_%s_send_push_notification' % (opts.app_label, opts.model_name))
        })

        return context


class SloopAdminMixin(object):
    """
    Sloop admin mixin for sending push notifications
    """
    def get_urls(self):
        urls = super(SloopAdminMixin, self).get_urls()
        return [
            url(r'^send-push-notification/$', self.admin_site.admin_view(self.push_notification_view),
                name='%s_%s_send_push_notification' % (self.model._meta.app_label, self.model._meta.model_name))
        ] + urls

    def get_receivers_queryset(self, receiver_ids):
        """
        Filter your queryset as you want, then return it.
        """
        return receiver_ids

    def push_notification_view(self, request):
        push_notification_view = PushNotificationView.as_view()
        return push_notification_view(request, model_admin=self)

    def send_push_notification(self, request, queryset):
        # Action method.

        admin_site = self.admin_site
        opts = self.model._meta
        receivers = list(queryset.values_list('id', flat=True))
        form = PushNotificationForm(initial={'receivers': json.dumps(receivers)})

        context = {
            'form': form,
            'admin_site': admin_site.name,
            'title': 'Send Push Notification',
            'opts': opts,
            'app_label': opts.app_label,
            'view_url': reverse('admin:%s_%s_send_push_notification' % (opts.app_label, opts.model_name))
        }

        return TemplateResponse(request, 'django_sloop/push_notification.html', context=context)


class DeviceAdmin(admin.ModelAdmin):

    list_display = ["user", "platform", "model", "is_sandbox_enabled", "deleted_at", "date_created", "date_updated"]
    readonly_fields = ["user", "platform", "model", "deleted_at", "date_created", "date_updated"]
    search_fields = ["user_id"]

    def save_model(self, request, obj, form, change):
        # Clear sns_platform_endpoint_arn if sandbox mode is changed.
        # https://docs.djangoproject.com/en/2.2/ref/models/instances/#refreshing-objects-from-database
        new_value = obj.is_sandbox_enabled
        delattr(obj, "is_sandbox_enabled")
        # Fetch field from database.
        old_value = obj.is_sandbox_enabled

        if new_value != old_value:
            obj.sns_platform_endpoint_arn = ""

        obj.is_sandbox_enabled = new_value

        super(DeviceAdmin, self).save_model(request, obj, form, change)


class PushMessageAdmin(admin.ModelAdmin):

    search_fields = ["body", "sns_message_id"]
    list_display = ["id", "body", "error_message", "device", "sns_message_id", "date_created", "date_updated"]
    readonly_fields = ["id", "device",  "body",  "data", "sns_message_id", "sns_response", "payload", "date_created", "date_updated"]

    actions = ["resend_push_notification"]

    def error_message(self, obj):
        error = json.loads(obj.sns_response).get("Error")
        if error:
            return error.get("Message")

    def resend_push_notification(self, request, queryset):
        if queryset.count() > 1:
            messages.add_message(request, messages.ERROR, _("You can only send one push message at a time."))
        push_message = queryset.get()

        try:
            handler = SNSHandler(device=push_message.device)
            handler._send_payload(data=json.loads(push_message.data))
            messages.add_message(request, messages.SUCCESS, _("Push message has been sent."))
        except Exception as exc:
            messages.add_message(request, messages.ERROR, str(exc))

    def resend_push_notification(self, request, queryset):
        if queryset.count() > 1:
            messages.add_message(request, messages.ERROR, _("You can only send one push message at a time."))
        push_message = queryset.get()
        device = push_message.device
        try:
            payload = self.payload(push_message)
            payload = payload.get("data") or payload.get("aps")

            message = payload.get("alert")
            sound = payload.get("sound")
            extra = payload.get("custom")
            badge_count = payload.get("badge")
            category = payload.get("category")
            if message:
                device.send_push_notification(message, url=extra.get("url"), badge_count=badge_count, sound=sound, extra=extra, category=category)
                messages.add_message(request, messages.SUCCESS, _("Push message has been sent."))
            else:
                device.send_silent_push_notification(extra=extra, badge_count=badge_count, content_available=None)
                messages.add_message(request, messages.SUCCESS, _("Silent push message has been sent."))
        except Exception as exc:
            messages.add_message(request, messages.ERROR, str(exc))

    def payload(self, push_message):
        payload = json.loads(push_message.data)
        payload = payload.get("GCM") or payload.get("APNS") or payload.get("APNS_SANDBOX")
        payload = json.loads(payload)
        return payload


admin.site.register(PushMessage, PushMessageAdmin)
