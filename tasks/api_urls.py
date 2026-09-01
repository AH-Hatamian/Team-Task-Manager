from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    TeamDetailAPIView, TeamListCreateView, TaskListCreateView, TaskDetailAPIView, 
    TeamTaskListCreateView, MembershipListCreateView, MembershipDetailAPIView,
    CommentListCreateView, CommentDetailAPIView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# router = DefaultRouter()
# router.register(r'teams', TeamViewSet, basename='team')
# router.register(r'tasks', TaskViewSet, basename='task')
# router.register(r'memberships', MembershipViewSet, basename='membership')
# router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path("teams/", TeamListCreateView.as_view(), name="teams"),
    path("teams/<int:pk>/", TeamDetailAPIView.as_view(), name="team-detail"),

    path("teams/<int:pk>/tasks/", TeamTaskListCreateView.as_view(), name='team-tasks'),
    path("tasks/", TaskListCreateView.as_view(), name="tasks"),
    path("tasks/<int:pk>/", TaskDetailAPIView.as_view(), name="task-detail"),

    path("teams/<int:pk>/memberships/", MembershipListCreateView.as_view(), name="teams-memberships"),
    path("memberships/<int:pk>/", MembershipDetailAPIView.as_view(), name="membership-detail"),

    path("tasks/<int:pk>/comments/", CommentListCreateView.as_view(), name="task-comments"),
    path("comments/<int:pk>/", CommentDetailAPIView.as_view(), name="comment-detail"),

]