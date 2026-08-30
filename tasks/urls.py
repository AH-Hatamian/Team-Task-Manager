from django.urls import path
from . import views 

app_name = "tasks"

urlpatterns = [
    path("", views.TeamListView.as_view(), name="team_list"),
    path("my_tasks/", views.MyTasksView.as_view(), name="my_tasks"),
    path("team_detail/<int:pk>/", views.TeamDetailView.as_view(), name="team_detail"),
    path("team_detail/<int:pk>/task_list", views.TaskListView.as_view(), name="task_list"),
]