from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
@admin.register(User)
class KAPDAUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("KAPDA staff profile", {"fields": ("phone","reg_no","role","job_title","department","photo","projects","must_change_password")}),)
    list_display = ("username","email","phone","reg_no","role","job_title","is_staff","is_active")
    search_fields = ("username","email","phone","reg_no","first_name","last_name")
