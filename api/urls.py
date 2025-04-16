from django.urls import path
from .views import ProjectList, ProjectDetail, TaskList, TaskDetail, RemoveLeaderView, RemoveUserFromProjectView

from .views import RegisterUserView
urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('projects/', ProjectList.as_view()),
    path('projects/<int:pk>/', ProjectDetail.as_view()),
    path('projects/<int:project_id>/tasks/', TaskList.as_view()),
    path('tasks/<int:pk>/', TaskDetail.as_view()),
    path('projects/<int:project_id>/remove-leader/', RemoveLeaderView.as_view()),
    path('projects/<int:project_id>/remove-user/<int:user_id>/', RemoveUserFromProjectView.as_view()),
]
