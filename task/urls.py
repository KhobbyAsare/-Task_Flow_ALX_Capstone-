from django.urls import path
from .views import (
    TaskCreateAPIView,
    TaskListAPIView,
    TaskRetrieveAPIView,
    TaskUpdateAPIView,
    TaskDestroyAPIView,
    UserTaskStatsAPIView
)

app_name = 'task'

urlpatterns = [
    # Task CRUD endpoints
    path('create/', TaskCreateAPIView.as_view(), name='task-create'),
    path('list/', TaskListAPIView.as_view(), name='task-list'),
    path('<int:id>/', TaskRetrieveAPIView.as_view(), name='task-detail'),
    path('<int:id>/update/', TaskUpdateAPIView.as_view(), name='task-update'),
    path('<int:id>/delete/', TaskDestroyAPIView.as_view(), name='task-delete'),
    
    # Additional endpoints
    path('stats/', UserTaskStatsAPIView.as_view(), name='task-stats'),
]
