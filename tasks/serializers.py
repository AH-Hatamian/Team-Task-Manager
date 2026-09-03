from rest_framework import serializers
from .models import Team, Task, Membership, Comment

class TeamSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ["id", "name", "description", "created_at", "member_count"]
        read_only_fields = ["created_at"]

    def get_member_count(self, obj):
        return obj.memberships.count()

class TaskSerializer(serializers.ModelSerializer):
    assignee_username = serializers.CharField(source='assignee.username', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title", "description", "team_name","assignee", "assignee_username", "status", "created_by_name", "created_at"]
        read_only_fields = ["created_at", "created_by"]

    def validate(self, data):
        team = self.context.get("team")
        assignee = data.get("assignee")
    
        if team and assignee:
            is_member = Membership.objects.filter(team=team, user=assignee).exists()
            if not is_member:
                raise serializers.ValidationError(
                    {"assignee": "user is not a member of this team"}
                )
        return data    
    
class MembershipSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)
    class Meta:
        model = Membership
        fields = ["id", "team_name", "user", "user_name", "role"]

    def validate(self, data):
        member = data.get("user")
        team = self.context.get("team")

        if team and member:
            is_member = Membership.objects.filter(team = team, user = member).exists()
            if is_member:
                raise serializers.ValidationError(
                    {"user": f"user is already a member of team '{team.name}'"}
                )
        return data

class MembershipRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ["id", "role"]

class CommentSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="task.title", read_only = True)
    author_name = serializers.CharField(source='author.username', read_only=True)
    class Meta:
        model = Comment
        fields = ["id", "task_title", "author_name", "body", "created_at"]