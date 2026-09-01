from rest_framework import permissions
from .models import Membership, Team


def get_user_role(user, team):
    membership = Membership.objects.filter(team=team, user=user).first()
    return membership.role if membership else None


class TeamPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user, obj)

        if request.method == "DELETE":
            return role == Membership.Role.OWNER

        if request.method in ["PUT", "PATCH"]:
            return role in [Membership.Role.OWNER, Membership.Role.ADMIN]

        return role is not None


class TaskPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user, obj.team)
        is_creator = (obj.created_by == request.user)

        if request.method in ["PUT", "PATCH", "DELETE"]:
            return role in [Membership.Role.OWNER, Membership.Role.ADMIN] or is_creator

        return role is not None


class MembershipPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            team_id = view.kwargs.get("pk")
            team = Team.objects.get(pk=team_id)
            role = get_user_role(request.user, team)
            return role in [Membership.Role.OWNER, Membership.Role.ADMIN]
        return True

    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user, obj.team)

        if request.method in ["PUT", "PATCH"]:
            return role == Membership.Role.OWNER

        if request.method == "DELETE":
            if role == Membership.Role.OWNER:
                return True
            if role == Membership.Role.ADMIN:
                return obj.role == Membership.Role.MEMBER
            return False

        return role is not None


class CommentPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user, obj.task.team)
        is_author = (obj.author == request.user)

        if request.method in ["PUT", "PATCH"]:
            return is_author

        if request.method == "DELETE":
            return role in [Membership.Role.OWNER, Membership.Role.ADMIN] or is_author

        return role is not None