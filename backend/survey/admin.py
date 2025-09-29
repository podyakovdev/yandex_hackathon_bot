from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительные поля", {"fields": ("phone_number",)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)


