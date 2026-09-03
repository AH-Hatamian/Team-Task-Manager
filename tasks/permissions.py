from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import Membership, Team, Task


def get_user_role(user, team):
    membership = Membership.objects.filter(team=team, user=user).first()
    return membership.role if membership else None

class TeamDetailPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user, obj)

        if request.method == "DELETE":
            return role == Membership.Role.OWNER

        if request.method in ["PUT", "PATCH"]:
            return role in [Membership.Role.OWNER, Membership.Role.ADMIN]

        return role is not None

class TaskListPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        team_id = view.kwargs.get("pk")
        get_object_or_404(Team, pk=team_id, members=request.user)
        return True

class TaskDetailPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user, obj.team)
        is_creator = (obj.created_by == request.user)

        if request.method in ["PUT", "PATCH", "DELETE"]:
            return role in [Membership.Role.OWNER, Membership.Role.ADMIN] or is_creator

        return role is not None

class MembershipListPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        team_id = view.kwargs.get("pk")
        team = get_object_or_404(Team, pk=team_id, members=request.user)
        
        if request.method == "POST":
            role = get_user_role(request.user, team)
            return role in [Membership.Role.OWNER, Membership.Role.ADMIN]
            
        return True

class MembershipDetailPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user, obj.team)

        if request.method in ["PUT", "PATCH"]:
            return role == Membership.Role.OWNER

        if request.method == "DELETE":
            if role == Membership.Role.OWNER:
                return obj.role != Membership.Role.OWNER
            if role == Membership.Role.ADMIN:
                return obj.role == Membership.Role.MEMBER
            return False

        return role is not None


class CommentListPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        task_id = view.kwargs.get("pk")
        get_object_or_404(Task, pk=task_id, team__members=request.user)
        return True    

class CommentDetailPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user, obj.task.team)
        is_author = (obj.author == request.user)

        if request.method in ["PUT", "PATCH"]:
            return is_author

        if request.method == "DELETE":
            return role in [Membership.Role.OWNER, Membership.Role.ADMIN] or is_author

        return role is not None