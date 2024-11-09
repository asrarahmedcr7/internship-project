from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Client, Engagement

# Register Client model with the Django admin using the built-in UserAdmin
@admin.register(Client)
class ClientAdmin(UserAdmin):
    # Add custom fields to display in the admin interface
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('organization',)}),  # Add any additional fields
    )
    list_display = ('username', 'email', 'organization', 'is_staff', 'is_active')
    search_fields = ('username', 'email')

# Register Engagement model with the Django admin
@admin.register(Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ('engagement_title', 'client')
    search_fields = ('engagement_title', 'client__username')