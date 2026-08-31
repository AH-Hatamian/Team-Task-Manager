from django.urls import path
from . import views 

app_name = "tasks"

urlpatterns = [
    path("", views.TeamListView.as_view(), name="team_list"),
    path("my_tasks/", views.MyTasksView.as_view(), name="my_tasks"),
    path("team_detail/<int:pk>/", views.TeamDetailView.as_view(), name="team_detail"),
    path("team_detail/<int:pk>/task_list/", views.TaskListView.as_view(), name="task_list"),
    path("team_detail/<int:pk>/task_list/add_task/", views.CreateTaskView.as_view(), name="add_task"),
    path("<int:pk>/edit/", views.TaskUpdateView.as_view(), name="edit_task"),
    path("<int:pk>/delete/", views.DeleteTaskView.as_view(), name="delete_task"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("<int:pk>/comments/", views.CommentListView.as_view(), name="comment_list"),
    path("<int:pk>/comments/add_comment", views.CreateCommentView.as_view(), name="add_comment")
]