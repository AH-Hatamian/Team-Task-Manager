from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DeleteView, DetailView, UpdateView, CreateView
from django.urls import reverse, reverse_lazy
from .models import Membership, Task, Team
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import TaskForm, LogInForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages


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

class CreateTaskView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Task
    form_class = TaskForm
    teamplate_name = "task_form.html"

    def get_team(self):
        return get_object_or_404(Team, pk=self.kwargs["pk"])

    def test_func(self):
        team = self.get_team()
        return team.memberships.filter(user=self.request.user).exists()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["team"] = self.get_team()
        return kwargs

    def form_valid(self, form):
        form.instance.team = self.get_team()
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("tasks:task_list", kwargs={"pk": self.get_team().pk})

class CreateTaskView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Task
    form_class = TaskForm
    teamplate_name = "task_form.html"

    def get_team(self):
        return get_object_or_404(Team, pk=self.kwargs["pk"])

    def test_func(self):
        team = self.get_team()
        return team.memberships.filter(user=self.request.user).exists()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["team"] = self.get_team()
        return kwargs

    def form_valid(self, form):
        form.instance.team = self.get_team()
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("tasks:task_list", kwargs={"pk": self.get_team().pk})


class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def test_func(self):
        task = self.get_object()
        membership = task.team.memberships.filter(user=self.request.user).first()
        return membership is not None and membership.role in (Membership.Role.OWNER, Membership.Role.ADMIN)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["team"] = self.get_object().team
        return kwargs
            
    def get_success_url(self):
        return reverse("tasks:task_list", kwargs={"pk": self.object.team.pk})

class DeleteTaskView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Task
    template_name = "tasks/delete_task.html"

    def test_func(self):
        task = self.get_object()
        membership = task.team.memberships.filter(user=self.request.user).first()
        return membership is not None and membership.role in (Membership.Role.OWNER, Membership.Role.ADMIN)

    def get_success_url(self):
            return reverse("tasks:task_list", kwargs={"pk": self.object.team.pk})

def login_view(request):
    if request.method == "POST":
        form = LogInForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("tasks:team_list")
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LogInForm()
    return render(request, "tasks/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("tasks:login")
