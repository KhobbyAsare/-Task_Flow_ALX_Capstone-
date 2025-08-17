from django.urls import path
from .views import (
    TaskCreateAPIView,
    TaskListAPIView,
    TaskRetrieveAPIView,
    TaskUpdateAPIView,
    TaskDestroyAPIView,
    UserTaskStatsAPIView,
    TaskCategoriesAPIView,
    TasksByCategoryAPIView,
    TasksByPriorityAPIView,
    UrgentTasksAPIView,
    TaskPrioritiesAPIView,
    BulkTaskStatusUpdateAPIView,
    CompletedTasksAPIView,
    PendingTasksAPIView,
    TaskDashboardAPIView
)

app_name = 'task'

urlpatterns = [
    # Task CRUD endpoints
    path('create/', TaskCreateAPIView.as_view(), name='task-create'),
    path('list/', TaskListAPIView.as_view(), name='task-list'),
    path('<int:id>/', TaskRetrieveAPIView.as_view(), name='task-detail'),
    path('<int:id>/update/', TaskUpdateAPIView.as_view(), name='task-update'),
    path('<int:id>/delete/', TaskDestroyAPIView.as_view(), name='task-delete'),
    
    # Task Organization endpoints
    path('categories/', TaskCategoriesAPIView.as_view(), name='task-categories'),
    path('categories/<str:category>/', TasksByCategoryAPIView.as_view(), name='tasks-by-category'),
    path('priorities/', TaskPrioritiesAPIView.as_view(), name='task-priorities'),
    path('priorities/<str:priority>/', TasksByPriorityAPIView.as_view(), name='tasks-by-priority'),
    
    # Task Status endpoints
    path('completed/', CompletedTasksAPIView.as_view(), name='completed-tasks'),
    path('pending/', PendingTasksAPIView.as_view(), name='pending-tasks'),
    path('urgent/', UrgentTasksAPIView.as_view(), name='urgent-tasks'),
    path('bulk-update/', BulkTaskStatusUpdateAPIView.as_view(), name='bulk-task-update'),
    
    # Dashboard and Stats endpoints
    path('dashboard/', TaskDashboardAPIView.as_view(), name='task-dashboard'),
    path('stats/', UserTaskStatsAPIView.as_view(), name='task-stats'),
]
