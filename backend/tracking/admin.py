from django.contrib import admin
from .models import Visitor

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ["id", "created_at", "last_seen", "user_agent"]
    readonly_fields = ["created_at", "last_seen", "user_agent"]
    search_fields = ["user_agent"]

    def has_add_permission(self, request):
        """
        Prevent creation of visitor records through the admin interface.
        This is to ensure that visitors are only created through the API endpoint.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of visitor records through the admin interface.
        In the future, this will happen automatically via a cron job.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        Prevent modification of visitor records through the admin interface.
        """
        return False
