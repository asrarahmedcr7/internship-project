from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Client, Engagement, ClientUser

# Register ClientUser model with the Django admin using the built-in UserAdmin
@admin.register(ClientUser)
class ClientUserAdmin(UserAdmin):
    # Add custom fields to display in the admin interface
    list_display = ('id', 'username', 'client', 'email', 'date_joined')
    
    # Add the ForeignKey field 'client' in the fieldsets for add/edit form
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('client',)}),
    )

    # Search fields for ClientUser model
    search_fields = ('username', 'email', 'client__name')  # Corrected to use client__name if `name` is the field in Client

# Register Client model with the Django admin (for managing client-related information)
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email')  # Ensure 'name' exists in Client model
    search_fields = ('name', 'email')

# Register Engagement model with the Django admin
@admin.register(Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ('id', 'engagement_id', 'engagement_title', 'client')
    search_fields = ('engagement_title', 'client__name')  # client__name for ForeignKey search