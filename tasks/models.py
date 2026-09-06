from django.db import models
from django.conf import settings

USER_MODEL = settings.AUTH_USER_MODEL

class Team(models.Model):

    class Meta:
        ordering = ['-created_at']

    name = models.CharField(max_length= 255)
    description = models.TextField(blank= True)
    created_at = models.DateTimeField(auto_now_add=True)

    members = models.ManyToManyField(USER_MODEL, through="Membership", related_name="teams")

    def __str__(self):
        return self.name

class Membership(models.Model):

    class Meta:
        ordering = ['-joined_at']
        constraints = [
            models.UniqueConstraint(fields=["team", "user"], name="unique_team_membership")
        ]

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE, related_name="memberships")

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER, db_index=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} in {self.team} as {self.role}"

class Task(models.Model):

    class Meta:
        ordering = ['-created_at']

    class Status(models.TextChoices):
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE =  "done", "Done"
         
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="tasks")
    assignee = models.ForeignKey(USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="assigned_tasks")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.TODO, db_index=True)
    created_by = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE, related_name="created_tasks")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.body} -- Comment by {self.author} on {self.task}"
                

    @property
    def team(self):
        return self.task.team

        
from django.db.models.signals import post_delete
from django.dispatch import receiver

@receiver(post_delete, sender=Membership)
def remove_assignee_from_tasks(sender, instance, **kwargs):

    Task.objects.filter(
        team=instance.team,
        assignee=instance.user
    ).update(assignee=None)