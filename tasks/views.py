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
    template_name = "task_form.html"

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

from django.db.models import Count
from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from .models import Team, Task
from rest_framework.response import Response
from .serializers import TaskSerializer, MembershipSerializer, TeamSerializer, CommentSerializer, MembershipRoleUpdateSerializer
from .permissions import (
    TeamDetailPermission,
    TaskListPermission, TaskDetailPermission,
    MembershipListPermission,
    MembershipDetailPermission,
    CommentListPermission,
    CommentDetailPermission,
    TransferOwnershipPermission
)

class TeamListCreateView(generics.ListCreateAPIView):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        return Team.objects.filter(members = self.request.user).annotate(
            member_count_annotated=Count('memberships')
        )

    def perform_create(self, serializer):
        team = serializer.save()
        Membership.objects.create(
            team=team,
            user=self.request.user,
            role=Membership.Role.OWNER
        )

class TeamTaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, TaskListPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'assignee']
    search_fields = ["title"]

    def get_queryset(self):
        team_id = self.kwargs["pk"]
        return Task.objects.filter(team_id = team_id, team__members = self.request.user).select_related('assignee', 'created_by', 'team')

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
    permission_classes = [permissions.IsAuthenticated, TeamDetailPermission]

    def get_queryset(self):
        return Team.objects.filter(members = self.request.user)


class TaskListCreateView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user).select_related('assignee', 'created_by', 'team')

    

    # def perform_create(self, serializer):
    #     team_id = self.kwargs["pk"]
    #     team = Team.objects.get(pk=team_id)
    #     serializer.save(team=team, created_by=self.request.user)


class TaskDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, TaskDetailPermission]

    def get_queryset(self):
        return Task.objects.filter(
            team__memberships__user=self.request.user
        )
class MembershipListCreateView(generics.ListCreateAPIView):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated, MembershipListPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['role']
    search_fields = ["user__username"]
        
    def get_team(self):
        if not hasattr(self, '_team'):
            team_id = self.kwargs["pk"]
            self._team = get_object_or_404(
                Team.objects.filter(members=self.request.user),
                pk=team_id
            )
        return self._team

    def get_queryset(self):
        return Membership.objects.filter(
            team=self.get_team()
        ).select_related('user', 'team')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["team"] = self.get_team()
        return context

    def perform_create(self, serializer):
        serializer.save(team=self.get_team(), role=Membership.Role.MEMBER)

class MembershipDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated, MembershipDetailPermission]
    
    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return MembershipRoleUpdateSerializer
        return MembershipSerializer
    
    def get_queryset(self):
        return Membership.objects.filter(
            team__memberships__user=self.request.user
        )

class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, CommentListPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["body"]

    def get_queryset(self):
        task_id = self.kwargs["pk"]
        return Comment.objects.filter(
            task_id=task_id,
            task__team__memberships__user=self.request.user
        ).select_related('author', 'task')

    def perform_create(self, serializer):
        task_id = self.kwargs["pk"]
        task = Task.objects.get(pk = task_id)
        serializer.save(task = task, author=self.request.user)


class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, CommentDetailPermission]

    def get_queryset(self):
        return Comment.objects.filter(
            task__team__memberships__user=self.request.user
        )


class TransferOwnershipView(APIView):
    permission_classes = [permissions.IsAuthenticated, TransferOwnershipPermission]

    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk, members=request.user)
        self.check_object_permissions(request, team)

        new_owner_id = request.data.get("new_owner")
        if not new_owner_id:
            return Response(
                {"detail": "new_owner is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_owner_membership = Membership.objects.filter(
            team=team, user_id=new_owner_id
        ).first()

        if not new_owner_membership:
            return Response(
                {"detail": "User is not a member of this team."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_owner_membership.role == Membership.Role.MEMBER:
            return Response(
                {"detail": "New owner must be an existing Admin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_owner_membership.user == request.user:
            return Response(
                {"detail": "You are already the owner."},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_owner_membership = Membership.objects.get(team=team, user=request.user)

        with transaction.atomic():
            old_owner_membership.role = Membership.Role.ADMIN
            old_owner_membership.save()

            new_owner_membership.role = Membership.Role.OWNER
            new_owner_membership.save()

        return Response(
            {"detail": "Ownership transferred successfully."},
            status=status.HTTP_200_OK
        )



