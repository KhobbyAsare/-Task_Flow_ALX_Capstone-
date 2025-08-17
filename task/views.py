from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Task
from .serializers import (
    TaskSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskListSerializer,
    TaskDetailSerializer
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
