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
from .dashboard_views import (
    dashboard_view, task_list_view, task_calendar_view, task_calendar_api,
    task_create_view, task_detail_view, task_edit_view, task_delete_view,
    toggle_task_complete, task_stats_api, register_view
)

app_name = 'task'

urlpatterns = [
    # Web Dashboard and Views
    path('', dashboard_view, name='dashboard'),
    path('web/dashboard/', dashboard_view, name='web_dashboard'),
    path('web/tasks/', task_list_view, name='web_task_list'),
    path('web/calendar/', task_calendar_view, name='web_task_calendar'),
    
    # Web Task CRUD operations
    path('web/tasks/create/', task_create_view, name='web_task_create'),
    path('web/tasks/<int:task_id>/', task_detail_view, name='web_task_detail'),
    path('web/tasks/<int:task_id>/edit/', task_edit_view, name='web_task_edit'),
    path('web/tasks/<int:task_id>/delete/', task_delete_view, name='web_task_delete'),
    
    # Web Task actions
    path('web/tasks/<int:task_id>/toggle/', toggle_task_complete, name='web_task_toggle'),
    
    # Web API endpoints
    path('web/tasks/calendar/api/', task_calendar_api, name='web_task_calendar_api'),
    path('web/api/stats/', task_stats_api, name='web_task_stats_api'),
    
    # API endpoints (existing)
    path('api/create/', TaskCreateAPIView.as_view(), name='task-create'),
    path('api/list/', TaskListAPIView.as_view(), name='task-list'),
    path('api/<int:id>/', TaskRetrieveAPIView.as_view(), name='task-detail'),
    path('api/<int:id>/update/', TaskUpdateAPIView.as_view(), name='task-update'),
    path('api/<int:id>/delete/', TaskDestroyAPIView.as_view(), name='task-delete'),
    
    # Task Organization endpoints (API)
    path('api/categories/', TaskCategoriesAPIView.as_view(), name='task-categories'),
    path('api/categories/<str:category>/', TasksByCategoryAPIView.as_view(), name='tasks-by-category'),
    path('api/priorities/', TaskPrioritiesAPIView.as_view(), name='task-priorities'),
    path('api/priorities/<str:priority>/', TasksByPriorityAPIView.as_view(), name='tasks-by-priority'),
    
    # Task Status endpoints (API)
    path('api/completed/', CompletedTasksAPIView.as_view(), name='completed-tasks'),
    path('api/pending/', PendingTasksAPIView.as_view(), name='pending-tasks'),
    path('api/urgent/', UrgentTasksAPIView.as_view(), name='urgent-tasks'),
    path('api/bulk-update/', BulkTaskStatusUpdateAPIView.as_view(), name='bulk-task-update'),
    
    # Dashboard and Stats endpoints (API)
    path('api/dashboard/', TaskDashboardAPIView.as_view(), name='task-dashboard'),
    path('api/stats/', UserTaskStatsAPIView.as_view(), name='task-stats'),
]
