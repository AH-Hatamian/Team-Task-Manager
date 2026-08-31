from django import forms
from .models import Task, Team, USER_MODEL

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "status", "assignee"]

    def __init__(self, *args, team=None, **kwargs):
        super().__init__(*args, **kwargs)
        if team is not None:
            self.fields["assignee"].queryset = team.members.all()

class LogInForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
