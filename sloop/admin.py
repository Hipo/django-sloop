from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.views.generic import FormView
from django.template.response import TemplateResponse
from django import forms

import json


class PushNotificationForm(forms.Form):
    message = forms.CharField(max_length=255, label='Message:')
    extra = forms.CharField(max_length=255, widget=forms.Textarea, required=False,
                            initial=json.dumps(dict()), label='Data as JSON:')
    url = forms.URLField(max_length=255, required=False, label='URL:', initial='http://')
    receivers = forms.CharField(widget=forms.HiddenInput)

    def clean(self):
        try:
            self.cleaned_data['extra'] = json.loads(self.cleaned_data['extra'])
            self.cleaned_data['receivers'] = json.loads(self.cleaned_data['receivers'])
        except (TypeError, ValueError) as ex:
            self.add_error('extra', ex.message)
        except KeyError:
            self.add_error(None, 'Could not retrieve push notification receivers, please try again.')

        return self.cleaned_data


class PushNotificationView(FormView):
    template_name = 'push_notification.html'
    form_class = PushNotificationForm

    def form_valid(self, form):
        receivers = form.cleaned_data['receivers']
        filtered_queryset = self.model_admin.get_receivers_queryset(receivers)
        for user in filtered_queryset:
            user.send_push_notification(form.cleaned_data['message'],
                                        extra=form.cleaned_data['extra'])

        return super(PushNotificationView, self).form_valid(form)

    def get_success_url(self):
        model_admin = self.kwargs.get('model_admin')
        return reverse('admin:%s_%s_changelist' % (model_admin.model._meta.app_label,
                                                   model_admin.model._meta.model_name))

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
    def get_push_notification_urls(self):
        # urls = super(SloopAdminMixin, self).get_urls()
        custom_urls = patterns('',
            url(r'^send-push-notification/$', self.admin_site.admin_view(self.push_notification_view),
                name='%s_%s_send_push_notification' % (self.model._meta.app_label, self.model._meta.model_name))
        )
        return custom_urls

    def get_receivers_queryset(self, receiver_ids):
        """
        Filter your queryset as you want, then return it.
        """
        raise NotImplementedError('get_receivers_queryset must be implemented in order to send push notifications.')

    def push_notification_view(self, request):
        push_notification_view = PushNotificationView.as_view()
        push_notification_view.model_admin = self
        return push_notification_view(request, model_admin=self)

    def send_push_notification(self, request, queryset):
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

        return TemplateResponse(request, 'push_notification.html', context=context, current_app=admin_site.name)