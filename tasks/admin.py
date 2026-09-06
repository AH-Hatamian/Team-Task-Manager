from django.contrib import admin
from .models import Team, Membership, Task, Comment
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'is_staff', 'is_active')

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1
    
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at", "member_count"]
    search_fields = ["name"]
    inlines = [MembershipInline]

    def member_count(self, obj):
        return obj.memberships.count()

    member_count.short_description ="member count"

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["team", "user", "role", "joined_at"]
    list_filter = ["team", "role"]
    search_fields = ["user__name", "team__name"]

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "team", "status", "assignee", "created_by", "created_at"]
    list_filter = ["team", "status"]
    search_fields = ["title", "description"]
    autocomplete_fields = ["assignee", "created_by"]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["task", "author", "created_at"]
    list_filter = ["task__team",]
    search_fields = ["body",]

