from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DeleteView, DetailView, UpdateView
from django.urls import reverse, reverse_lazy
from .models import Membership, Task, Team
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = "team_list.html"
    context_object_name = "teams"

    def get_queryset(self):
        return Team.objects.filter(memberships__user = self.request.user).distinct()

class TeamDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Team
    template_name = "tasks/team_detail.html"
    context_object_name = "team"

    def test_func(self):
        team = self.get_object()
        return team.memberships.filter(user=self.request.user).exists()

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "task_list.html"
    context_object_name = "tasks"

    def get_team(self):
        return get_object_or_404(Team, pk=self.kwargs["pk"])

    def test_func(self):
        team = self.get_team()
        return team.memberships.filter(user=self.request.user).exists()

    def get_queryset(self):
        return Task.objects.filter(team=self.get_team()).select_related("assignee", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.get_team()
        return context

class MyTasksView(LoginRequiredMixin, ListView):
    
    model = Task
    template_name = "tasks/my_tasks.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return Task.objects.filter(assignee = self.request.user).distinct()


