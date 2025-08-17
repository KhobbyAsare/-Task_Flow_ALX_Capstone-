from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Task, Category
from .serializers import (
    TaskSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskListSerializer,
    TaskDetailSerializer,
    CategorySerializer,
    CategoryCreateSerializer,
    CategoryUpdateSerializer,
    CategoryListSerializer
)


class IsTaskOwner(IsAuthenticated):
    """
    Custom permission to only allow owners of a task to view/edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Permission is only allowed to the owner of the task
        return obj.user == request.user


class TaskCreateAPIView(generics.CreateAPIView):
    """
    Create a new task for the authenticated user
    """
    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Save the task with the current user as owner"""
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(user=request.user)
        
        # Return detailed task information
        response_serializer = TaskDetailSerializer(task)
        return Response(
            {
                'message': 'Task created successfully',
                'task': response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class TaskListAPIView(generics.ListAPIView):
    """
    List all tasks for the authenticated user with filtering options
    """
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['priority', 'category', 'is_completed']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return tasks only for the authenticated user"""
        queryset = Task.objects.filter(user=self.request.user)
        
        # Additional filtering options
        status_filter = self.request.query_params.get('status', None)
        due_filter = self.request.query_params.get('due', None)
        
        if status_filter == 'completed':
            queryset = queryset.filter(is_completed=True)
        elif status_filter == 'pending':
            queryset = queryset.filter(is_completed=False)
        
        if due_filter == 'today':
            from django.utils import timezone
            today = timezone.now().date()
            queryset = queryset.filter(due_date__date=today)
        elif due_filter == 'overdue':
            from django.utils import timezone
            queryset = queryset.filter(
                due_date__lt=timezone.now(),
                is_completed=False
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'message': 'Tasks retrieved successfully',
                'tasks': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'message': 'Tasks retrieved successfully',
            'count': queryset.count(),
            'tasks': serializer.data
        })


class TaskRetrieveAPIView(generics.RetrieveAPIView):
    """
    Retrieve a specific task for the authenticated user
    """
    queryset = Task.objects.all()
    serializer_class = TaskDetailSerializer
    permission_classes = [IsTaskOwner]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Return tasks only for the authenticated user"""
        return Task.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'message': 'Task retrieved successfully',
            'task': serializer.data
        })


class TaskUpdateAPIView(generics.UpdateAPIView):
    """
    Update a specific task for the authenticated user
    """
    queryset = Task.objects.all()
    serializer_class = TaskUpdateSerializer
    permission_classes = [IsTaskOwner]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Return tasks only for the authenticated user"""
        return Task.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return detailed task information
        response_serializer = TaskDetailSerializer(instance)
        return Response({
            'message': 'Task updated successfully',
            'task': response_serializer.data
        })
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class TaskDestroyAPIView(generics.DestroyAPIView):
    """
    Delete a specific task for the authenticated user
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsTaskOwner]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Return tasks only for the authenticated user"""
        return Task.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        task_title = instance.title
        self.perform_destroy(instance)
        return Response({
            'message': f'Task "{task_title}" deleted successfully'
        }, status=status.HTTP_200_OK)


class UserTaskStatsAPIView(generics.GenericAPIView):
    """
    Get task statistics for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user_tasks = Task.objects.filter(user=request.user)
        
        # Calculate statistics
        total_tasks = user_tasks.count()
        completed_tasks = user_tasks.filter(is_completed=True).count()
        pending_tasks = user_tasks.filter(is_completed=False).count()
        high_priority_tasks = user_tasks.filter(priority='HIGH', is_completed=False).count()
        
        # Overdue tasks
        from django.utils import timezone
        overdue_tasks = user_tasks.filter(
            due_date__lt=timezone.now(),
            is_completed=False
        ).count()
        
        # Tasks by category
        categories_stats = {}
        for choice in Task.CATEGORY_CHOICES:
            category_code = choice[0]
            category_name = choice[1]
            count = user_tasks.filter(category=category_code).count()
            categories_stats[category_name] = count
        
        return Response({
            'message': 'Task statistics retrieved successfully',
            'stats': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
                'high_priority_pending': high_priority_tasks,
                'overdue_tasks': overdue_tasks,
                'completion_rate': round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0,
                'categories': categories_stats
            }
        })


class TaskCategoriesAPIView(generics.GenericAPIView):
    """
    Get available task categories and their task counts
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user_tasks = Task.objects.filter(user=request.user)
        
        categories_data = []
        for choice in Task.CATEGORY_CHOICES:
            category_code = choice[0]
            category_name = choice[1]
            
            category_tasks = user_tasks.filter(category=category_code)
            total_count = category_tasks.count()
            completed_count = category_tasks.filter(is_completed=True).count()
            pending_count = category_tasks.filter(is_completed=False).count()
            
            categories_data.append({
                'code': category_code,
                'name': category_name,
                'total_tasks': total_count,
                'completed_tasks': completed_count,
                'pending_tasks': pending_count,
                'completion_rate': round((completed_count / total_count * 100), 2) if total_count > 0 else 0
            })
        
        return Response({
            'message': 'Task categories retrieved successfully',
            'categories': categories_data
        })


class TasksByCategoryAPIView(generics.ListAPIView):
    """
    Get tasks grouped by specific category
    """
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        category = self.kwargs.get('category')
        queryset = Task.objects.filter(user=self.request.user, category=category.upper())
        
        # Additional filtering
        status_filter = self.request.query_params.get('status', None)
        if status_filter == 'completed':
            queryset = queryset.filter(is_completed=True)
        elif status_filter == 'pending':
            queryset = queryset.filter(is_completed=False)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        category = self.kwargs.get('category')
        queryset = self.filter_queryset(self.get_queryset())
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Get category name
        category_name = dict(Task.CATEGORY_CHOICES).get(category.upper(), category)
        
        return Response({
            'message': f'Tasks for {category_name} category retrieved successfully',
            'category': {
                'code': category.upper(),
                'name': category_name,
                'total_tasks': queryset.count()
            },
            'tasks': serializer.data
        })


class TasksByPriorityAPIView(generics.ListAPIView):
    """
    Get tasks grouped by specific priority level
    """
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        priority = self.kwargs.get('priority')
        queryset = Task.objects.filter(user=self.request.user, priority=priority.upper())
        
        # Additional filtering
        status_filter = self.request.query_params.get('status', None)
        if status_filter == 'completed':
            queryset = queryset.filter(is_completed=True)
        elif status_filter == 'pending':
            queryset = queryset.filter(is_completed=False)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        priority = self.kwargs.get('priority')
        queryset = self.filter_queryset(self.get_queryset())
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Get priority name
        priority_name = dict(Task.PRIORITY_CHOICES).get(priority.upper(), priority)
        
        return Response({
            'message': f'{priority_name} priority tasks retrieved successfully',
            'priority': {
                'code': priority.upper(),
                'name': priority_name,
                'total_tasks': queryset.count()
            },
            'tasks': serializer.data
        })


class UrgentTasksAPIView(generics.ListAPIView):
    """
    Get urgent tasks (HIGH priority and/or overdue)
    """
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['due_date', '-created_at']
    
    def get_queryset(self):
        from django.utils import timezone
        now = timezone.now()
        
        user_tasks = Task.objects.filter(user=self.request.user, is_completed=False)
        
        # Get HIGH priority tasks or overdue tasks
        urgent_tasks = user_tasks.filter(
            Q(priority='HIGH') | Q(due_date__lt=now)
        ).distinct()
        
        return urgent_tasks
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        from django.utils import timezone
        now = timezone.now()
        
        # Separate high priority and overdue
        high_priority_count = queryset.filter(priority='HIGH').count()
        overdue_count = queryset.filter(due_date__lt=now).count()
        
        return Response({
            'message': 'Urgent tasks retrieved successfully',
            'summary': {
                'total_urgent': queryset.count(),
                'high_priority': high_priority_count,
                'overdue': overdue_count
            },
            'tasks': serializer.data
        })


class TaskPrioritiesAPIView(generics.GenericAPIView):
    """
    Get available task priorities and their task counts
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user_tasks = Task.objects.filter(user=request.user)
        
        priorities_data = []
        for choice in Task.PRIORITY_CHOICES:
            priority_code = choice[0]
            priority_name = choice[1]
            
            priority_tasks = user_tasks.filter(priority=priority_code)
            total_count = priority_tasks.count()
            completed_count = priority_tasks.filter(is_completed=True).count()
            pending_count = priority_tasks.filter(is_completed=False).count()
            
            priorities_data.append({
                'code': priority_code,
                'name': priority_name,
                'total_tasks': total_count,
                'completed_tasks': completed_count,
                'pending_tasks': pending_count,
                'completion_rate': round((completed_count / total_count * 100), 2) if total_count > 0 else 0
            })
        
        return Response({
            'message': 'Task priorities retrieved successfully',
            'priorities': priorities_data
        })


class BulkTaskStatusUpdateAPIView(generics.GenericAPIView):
    """
    Bulk update task completion status
    """
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, *args, **kwargs):
        task_ids = request.data.get('task_ids', [])
        is_completed = request.data.get('is_completed', None)
        
        if not task_ids:
            return Response(
                {'error': 'task_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if is_completed is None:
            return Response(
                {'error': 'is_completed is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get tasks belonging to the user
        tasks = Task.objects.filter(
            id__in=task_ids,
            user=request.user
        )
        
        if not tasks.exists():
            return Response(
                {'error': 'No valid tasks found for the provided IDs'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update tasks
        updated_count = tasks.count()
        for task in tasks:
            task.is_completed = is_completed
            task.save()  # This will trigger our custom save method
        
        action = 'completed' if is_completed else 'marked as pending'
        
        return Response({
            'message': f'{updated_count} tasks {action} successfully',
            'updated_count': updated_count,
            'task_ids': list(tasks.values_list('id', flat=True))
        })


class CompletedTasksAPIView(generics.ListAPIView):
    """
    Get all completed tasks for the user
    """
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['priority', 'category']
    search_fields = ['title', 'description']
    ordering_fields = ['completed_at', 'created_at', 'due_date']
    ordering = ['-completed_at']
    
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, is_completed=True)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'message': 'Completed tasks retrieved successfully',
            'total_completed': queryset.count(),
            'tasks': serializer.data
        })


class PendingTasksAPIView(generics.ListAPIView):
    """
    Get all pending (incomplete) tasks for the user
    """
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['priority', 'category']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'created_at', 'priority']
    ordering = ['due_date', '-created_at']
    
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, is_completed=False)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        from django.utils import timezone
        now = timezone.now()
        overdue_count = queryset.filter(due_date__lt=now).count()
        
        return Response({
            'message': 'Pending tasks retrieved successfully',
            'total_pending': queryset.count(),
            'overdue_count': overdue_count,
            'tasks': serializer.data
        })


class TaskDashboardAPIView(generics.GenericAPIView):
    """
    Comprehensive task dashboard with organization metrics
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        from django.utils import timezone
        now = timezone.now()
        user_tasks = Task.objects.filter(user=request.user)
        
        # Basic stats
        total_tasks = user_tasks.count()
        completed_tasks = user_tasks.filter(is_completed=True).count()
        pending_tasks = user_tasks.filter(is_completed=False).count()
        
        # Priority breakdown
        priority_stats = {}
        for priority_code, priority_name in Task.PRIORITY_CHOICES:
            priority_tasks = user_tasks.filter(priority=priority_code)
            priority_stats[priority_name.lower()] = {
                'total': priority_tasks.count(),
                'completed': priority_tasks.filter(is_completed=True).count(),
                'pending': priority_tasks.filter(is_completed=False).count()
            }
        
        # Category breakdown
        category_stats = {}
        for category_code, category_name in Task.CATEGORY_CHOICES:
            category_tasks = user_tasks.filter(category=category_code)
            category_stats[category_name.lower()] = {
                'total': category_tasks.count(),
                'completed': category_tasks.filter(is_completed=True).count(),
                'pending': category_tasks.filter(is_completed=False).count()
            }
        
        # Time-based stats
        today = now.date()
        this_week_start = today - timezone.timedelta(days=today.weekday())
        this_month_start = today.replace(day=1)
        
        overdue_tasks = user_tasks.filter(
            due_date__lt=now,
            is_completed=False
        ).count()
        
        due_today = user_tasks.filter(
            due_date__date=today,
            is_completed=False
        ).count()
        
        due_this_week = user_tasks.filter(
            due_date__date__range=[this_week_start, today + timezone.timedelta(days=6)],
            is_completed=False
        ).count()
        
        # Recent activity
        recent_completed = user_tasks.filter(
            is_completed=True,
            completed_at__gte=now - timezone.timedelta(days=7)
        ).count()
        
        recent_created = user_tasks.filter(
            created_at__gte=now - timezone.timedelta(days=7)
        ).count()
        
        # Productivity metrics
        completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0
        
        # Urgent tasks (HIGH priority + overdue)
        urgent_tasks_count = user_tasks.filter(
            Q(priority='HIGH', is_completed=False) | 
            Q(due_date__lt=now, is_completed=False)
        ).distinct().count()
        
        # Top categories by task count
        top_categories = []
        for category_code, category_name in Task.CATEGORY_CHOICES:
            count = user_tasks.filter(category=category_code).count()
            if count > 0:
                top_categories.append({
                    'name': category_name,
                    'count': count,
                    'completion_rate': round(
                        (user_tasks.filter(category=category_code, is_completed=True).count() / count * 100), 2
                    ) if count > 0 else 0
                })
        
        top_categories.sort(key=lambda x: x['count'], reverse=True)
        
        return Response({
            'message': 'Task dashboard data retrieved successfully',
            'dashboard': {
                'overview': {
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'pending_tasks': pending_tasks,
                    'completion_rate': completion_rate,
                    'urgent_tasks': urgent_tasks_count
                },
                'priorities': priority_stats,
                'categories': category_stats,
                'time_based': {
                    'overdue': overdue_tasks,
                    'due_today': due_today,
                    'due_this_week': due_this_week
                },
                'recent_activity': {
                    'completed_last_week': recent_completed,
                    'created_last_week': recent_created
                },
                'top_categories': top_categories[:5]  # Top 5 categories
            }
        })


# Custom Category CRUD Views
class IsCategoryOwner(IsAuthenticated):
    """
    Custom permission to only allow owners of a category to view/edit it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CustomCategoryCreateAPIView(generics.CreateAPIView):
    """
    Create a new custom category for the authenticated user
    """
    queryset = Category.objects.all()
    serializer_class = CategoryCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Save the category with the current user as owner"""
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save(user=request.user)
        
        # Return detailed category information
        response_serializer = CategorySerializer(category)
        return Response(
            {
                'message': 'Custom category created successfully',
                'category': response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class CustomCategoryListAPIView(generics.ListAPIView):
    """
    List all custom categories for the authenticated user
    """
    serializer_class = CategoryListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Return categories only for the authenticated user"""
        return Category.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'message': 'Custom categories retrieved successfully',
            'count': queryset.count(),
            'categories': serializer.data
        })


class CustomCategoryRetrieveAPIView(generics.RetrieveAPIView):
    """
    Retrieve a specific custom category for the authenticated user
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsCategoryOwner]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Return categories only for the authenticated user"""
        return Category.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'message': 'Category retrieved successfully',
            'category': serializer.data
        })


class CustomCategoryUpdateAPIView(generics.UpdateAPIView):
    """
    Update a specific custom category for the authenticated user
    """
    queryset = Category.objects.all()
    serializer_class = CategoryUpdateSerializer
    permission_classes = [IsCategoryOwner]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Return categories only for the authenticated user"""
        return Category.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return detailed category information
        response_serializer = CategorySerializer(instance)
        return Response({
            'message': 'Category updated successfully',
            'category': response_serializer.data
        })
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class CustomCategoryDestroyAPIView(generics.DestroyAPIView):
    """
    Delete a specific custom category for the authenticated user
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsCategoryOwner]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Return categories only for the authenticated user"""
        return Category.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        category_name = instance.name
        task_count = instance.task_set.count()
        
        if task_count > 0:
            return Response({
                'error': f'Cannot delete category "{category_name}" because it has {task_count} associated tasks. Please reassign or delete these tasks first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_destroy(instance)
        return Response({
            'message': f'Category "{category_name}" deleted successfully'
        }, status=status.HTTP_200_OK)


class AllCategoriesAPIView(generics.GenericAPIView):
    """
    Get all categories (default system categories + user's custom categories)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Get default system categories
        default_categories = []
        user_tasks = Task.objects.filter(user=request.user)
        
        for choice in Task.CATEGORY_CHOICES:
            category_code = choice[0]
            category_name = choice[1]
            
            category_tasks = user_tasks.filter(category=category_code)
            total_count = category_tasks.count()
            completed_count = category_tasks.filter(is_completed=True).count()
            pending_count = category_tasks.filter(is_completed=False).count()
            
            default_categories.append({
                'type': 'default',
                'code': category_code,
                'name': category_name,
                'total_tasks': total_count,
                'completed_tasks': completed_count,
                'pending_tasks': pending_count,
                'completion_rate': round((completed_count / total_count * 100), 2) if total_count > 0 else 0
            })
        
        # Get user's custom categories
        custom_categories = Category.objects.filter(user=request.user)
        custom_categories_data = CategoryListSerializer(custom_categories, many=True).data
        
        # Add type field to custom categories
        for category in custom_categories_data:
            category['type'] = 'custom'
        
        return Response({
            'message': 'All categories retrieved successfully',
            'categories': {
                'default': default_categories,
                'custom': custom_categories_data,
                'total_default': len(default_categories),
                'total_custom': len(custom_categories_data)
            }
        })
