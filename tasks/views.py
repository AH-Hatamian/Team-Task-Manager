from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DeleteView, DetailView, UpdateView, CreateView
from django.urls import reverse, reverse_lazy
from .models import Membership, Task, Team, Comment
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import TaskForm, LogInForm, CommentForm
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

    def is_admin_or_owner(self):
        team = self.get_team()
        membership = team.memberships.filter(user=self.request.user).first()
        return membership is not None and membership.role in (Membership.Role.OWNER, Membership.Role.ADMIN)

    def get_queryset(self):
        return Task.objects.filter(team=self.get_team()).select_related("assignee", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.get_team()
        context["allowed"] = self.is_admin_or_owner()
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
        membership = team.memberships.filter(user=self.request.user).first()
        return membership is not None and membership.role in (Membership.Role.OWNER, Membership.Role.ADMIN)


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

class CommentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Comment
    template_name = "tasks/comment_list.html"
    context_object_name = "comments"

    def get_task(self):
        return get_object_or_404(Task, pk=self.kwargs["pk"])

    def test_func(self):
        task = self.get_task()
        return task.team.memberships.filter(user=self.request.user).exists()

    def get_queryset(self):
        return Comment.objects.filter(task=self.get_task()).select_related("author")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task"] = self.get_task()
        return context

class CreateCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = "tasks/add_comment.html"

    def get_task(self):
        return get_object_or_404(Task, pk=self.kwargs["pk"])

    def test_func(self):
        team = self.get_task().team
        return team.memberships.filter(user=self.request.user).exists()

    def form_valid(self, form):
        form.instance.task = self.get_task()
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("tasks:comment_list", kwargs={"pk": self.object.task.pk})


from rest_framework import generics, permissions
from .models import Team, Task
from .serializers import TaskSerializer, MembershipSerializer, TeamSerializer, CommentSerializer
from .permissions import TeamPermission, TaskPermission, MembershipPermission, CommentPermission

class TeamListCreateView(generics.ListCreateAPIView):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Team.objects.filter(members = self.request.user)

    def perform_create(self, serializer):
        team = serializer.save()
        Membership.objects.create(
            team=team,
            user=self.request.user,
            role=Membership.Role.OWNER
        )

class TeamTaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        team_id = self.kwargs["pk"]
        return Task.objects.filter(team_id = team_id, team__members = self.request.user)

    def perform_create(self, serializer):
        team_id = self.kwargs["pk"]
        team = Team.objects.get(pk=team_id)
        serializer.save(team=team, created_by=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        team_id = self.kwargs["pk"]
        context["team"] = Team.objects.get(pk=team_id)
        return context
    

class TeamDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated, TeamPermission]

    def get_queryset(self):
        return Team.objects.filter(members = self.request.user)


class TaskListCreateView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)

    

    # def perform_create(self, serializer):
    #     team_id = self.kwargs["pk"]
    #     team = Team.objects.get(pk=team_id)
    #     serializer.save(team=team, created_by=self.request.user)


class TaskDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, TaskPermission]

    def get_queryset(self):
        return Task.objects.filter(
            team__memberships__user=self.request.user
        )

class MembershipListCreateView(generics.ListCreateAPIView):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated, MembershipPermission]

    def get_queryset(self):
        team_id = self.kwargs["pk"]
        return Membership.objects.filter(
            team_id=team_id,
            team__memberships__user=self.request.user
        )

    def perform_create(self, serializer):
        team_id = self.kwargs["pk"]
        team = Team.objects.get(pk=team_id)
        serializer.save(team=team)


class MembershipDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated, MembershipPermission]

    def get_queryset(self):
        return Membership.objects.filter(
            team__memberships__user=self.request.user
        )

class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        task_id = self.kwargs["pk"]
        return Comment.objects.filter(
            task_id=task_id,
            task__team__memberships__user=self.request.user
        )

    def perform_create(self, serializer):
        task_id = self.kwargs["pk"]
        task = Task.objects.get(pk = task_id)
        serializer.save(task = task, author=self.request.user)


class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, CommentPermission]

    def get_queryset(self):
        return Comment.objects.filter(
            task__team__memberships__user=self.request.user
        )

    
