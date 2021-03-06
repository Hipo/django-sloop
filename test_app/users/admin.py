from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from django_sloop.admin import SloopAdminMixin


class CustomUserAdmin(SloopAdminMixin, UserAdmin):
    actions = ("send_push_notification", )


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
