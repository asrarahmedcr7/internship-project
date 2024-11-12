from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Client, Engagement, ClientUser

# Register ClientUser model with the Django admin using the built-in UserAdmin
@admin.register(ClientUser)
class ClientUserAdmin(UserAdmin):
    # Add custom fields to display in the admin interface
    list_display = ('id', 'username', 'client_name', 'email', 'date_joined')

    def client_name(self, obj):
        return obj.client.name  # Reference to the Client model's name
    client_name.short_description = 'Client Name'

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('client',)}),  # Add the ForeignKey field 'client'
    )

    search_fields = ('client_name', 'email')

# Register Client model with the Django admin (for managing client-related information)
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email')
    search_fields = ('name', 'email')

# Register Engagement model with the Django admin
@admin.register(Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ('id', 'engagement_title', 'client')
    search_fields = ('id', 'engagement_title', 'client__name')