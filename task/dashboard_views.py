from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Task
from .serializers import TaskSerializer, TaskDetailSerializer
from .forms import TaskForm, CustomUserCreationForm
from authentication.models import UserProfile


@login_required
def dashboard_view(request):
    """
    Main dashboard view with task statistics and overview
    """
    user_tasks = Task.objects.filter(user=request.user)
    
    # Basic statistics
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(is_completed=True).count()
    pending_tasks = user_tasks.filter(is_completed=False).count()
    
    # Priority breakdown
    high_priority = user_tasks.filter(priority='HIGH', is_completed=False).count()
    medium_priority = user_tasks.filter(priority='MEDIUM', is_completed=False).count()
    low_priority = user_tasks.filter(priority='LOW', is_completed=False).count()
    
    # Overdue tasks
    now = timezone.now()
    overdue_tasks = user_tasks.filter(
        due_date__lt=now,
        is_completed=False
    ).count()
    
    # Tasks due today
    today = now.date()
    due_today = user_tasks.filter(
        due_date__date=today,
        is_completed=False
    ).count()
    
    # Recent tasks (last 7 days)
    week_ago = now - timedelta(days=7)
    recent_completed = user_tasks.filter(
        is_completed=True,
        completed_at__gte=week_ago
    ).count()
    
    recent_created = user_tasks.filter(
        created_at__gte=week_ago
    ).count()
    
    # Category stats
    category_stats = []
    for choice in Task.CATEGORY_CHOICES:
        category_code = choice[0]
        category_name = choice[1]
        count = user_tasks.filter(category=category_code).count()
        if count > 0:
            category_stats.append({
                'code': category_code,
                'name': category_name,
                'count': count,
                'completed': user_tasks.filter(category=category_code, is_completed=True).count()
            })
    
    # Recent tasks for display
    recent_tasks = user_tasks.order_by('-created_at')[:5]
    urgent_tasks = user_tasks.filter(
        Q(priority='HIGH', is_completed=False) | 
        Q(due_date__lt=now, is_completed=False)
    ).distinct()[:5]
    
    # Completion rate
    completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
    
    context = {
        'stats': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'high_priority': high_priority,
            'medium_priority': medium_priority,
            'low_priority': low_priority,
            'overdue_tasks': overdue_tasks,
            'due_today': due_today,
            'recent_completed': recent_completed,
            'recent_created': recent_created,
            'completion_rate': completion_rate,
        },
        'category_stats': category_stats,
        'recent_tasks': recent_tasks,
        'urgent_tasks': urgent_tasks,
        'page_title': 'Dashboard'
    }
    
    return render(request, 'task/dashboard.html', context)


@login_required
def task_list_view(request):
    """
    Task list view with sortable table and filtering
    """
    user_tasks = Task.objects.filter(user=request.user)
    
    # Apply filters
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search')
    
    if status_filter == 'completed':
        user_tasks = user_tasks.filter(is_completed=True)
    elif status_filter == 'pending':
        user_tasks = user_tasks.filter(is_completed=False)
    elif status_filter == 'overdue':
        user_tasks = user_tasks.filter(
            due_date__lt=timezone.now(),
            is_completed=False
        )
    
    if priority_filter and priority_filter.upper() in ['HIGH', 'MEDIUM', 'LOW']:
        user_tasks = user_tasks.filter(priority=priority_filter.upper())
    
    if category_filter and category_filter.upper() in [choice[0] for choice in Task.CATEGORY_CHOICES]:
        user_tasks = user_tasks.filter(category=category_filter.upper())
    
    if search_query:
        user_tasks = user_tasks.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Order tasks
    order_by = request.GET.get('order_by', '-created_at')
    valid_order_fields = ['title', 'due_date', 'priority', 'category', 'created_at', 'is_completed']
    
    if order_by.lstrip('-') in valid_order_fields:
        user_tasks = user_tasks.order_by(order_by)
    else:
        user_tasks = user_tasks.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(user_tasks, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'tasks': page_obj,
        'filters': {
            'status': status_filter,
            'priority': priority_filter,
            'category': category_filter,
            'search': search_query,
            'order_by': order_by
        },
        'categories': Task.CATEGORY_CHOICES,
        'priorities': Task.PRIORITY_CHOICES,
        'page_title': 'Task List'
    }
    
    return render(request, 'task/task_list.html', context)


@login_required
def task_calendar_view(request):
    """
    Calendar view for tasks using FullCalendar.js
    """
    context = {
        'page_title': 'Task Calendar'
    }
    return render(request, 'task/task_calendar.html', context)


@login_required
def task_calendar_api(request):
    """
    API endpoint for calendar events (FullCalendar.js integration)
    """
    user_tasks = Task.objects.filter(user=request.user)
    
    # Filter by date range if provided
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    if start_date and end_date:
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            user_tasks = user_tasks.filter(
                Q(due_date__gte=start, due_date__lte=end) |
                Q(created_at__gte=start, created_at__lte=end)
            )
        except ValueError:
            pass
    
    events = []
    for task in user_tasks:
        # Create event for due date if it exists
        if task.due_date:
            color = '#dc3545' if task.is_overdue else '#007bff'  # Red if overdue, blue otherwise
            if task.is_completed:
                color = '#28a745'  # Green if completed
            elif task.priority == 'HIGH':
                color = '#dc3545'  # Red for high priority
            elif task.priority == 'MEDIUM':
                color = '#ffc107'  # Yellow for medium priority
            else:
                color = '#17a2b8'  # Cyan for low priority
            
            events.append({
                'id': f'task_{task.id}',
                'title': task.title,
                'start': task.due_date.isoformat(),
                'color': color,
                'extendedProps': {
                    'taskId': task.id,
                    'description': task.description or '',
                    'priority': task.priority,
                    'category': task.category,
                    'completed': task.is_completed,
                    'overdue': task.is_overdue
                }
            })
    
    return JsonResponse(events, safe=False)


@login_required
def task_create_view(request):
    """
    Task creation view
    """
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            
            messages.success(request, f'Task "{task.title}" created successfully!')
            
            # Check if user wants to save and continue
            if 'save_and_continue' in request.POST:
                return redirect('task:web_task_create')
            else:
                return redirect('task:web_task_list')
    else:
        form = TaskForm()
    
    context = {
        'form': form,
        'page_title': 'Create New Task'
    }
    return render(request, 'task/task_create.html', context)


@login_required
def task_detail_view(request, task_id):
    """
    Task detail view
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    context = {
        'task': task,
        'page_title': f'Task: {task.title}'
    }
    return render(request, 'task/task_detail.html', context)


@login_required
@require_http_methods(["POST"])
def task_toggle_complete(request, task_id):
    """
    Toggle task completion status via AJAX
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    
    return JsonResponse({
        'success': True,
        'is_completed': task.is_completed,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None
    })


@login_required
@require_http_methods(["DELETE"])
def task_delete(request, task_id):
    """
    Delete task via AJAX
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task_title = task.title
    task.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Task "{task_title}" deleted successfully.'
    })


@login_required
def task_edit_view(request, task_id):
    """
    Task edit view
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('task:web_task_detail', task_id=task.id)
    else:
        form = TaskForm(instance=task)
    
    context = {
        'form': form,
        'task': task,
        'page_title': f'Edit Task: {task.title}'
    }
    return render(request, 'task/task_edit.html', context)


@login_required
def task_delete_view(request, task_id):
    """
    Task delete view (confirmation page)
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('task:web_task_list')
    
    context = {
        'task': task,
        'page_title': f'Delete Task: {task.title}'
    }
    return render(request, 'task/task_confirm_delete.html', context)


@login_required
def toggle_task_complete(request, task_id):
    """
    Toggle task completion status via AJAX
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    
    if task.is_completed:
        task.completed_at = timezone.now()
    else:
        task.completed_at = None
    
    task.save()
    
    return JsonResponse({
        'success': True,
        'is_completed': task.is_completed,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None
    })


@login_required
def task_stats_api(request):
    """
    API endpoint for task statistics (for dashboard widgets)
    """
    user_tasks = Task.objects.filter(user=request.user)
    now = timezone.now()
    
    stats = {
        'total_tasks': user_tasks.count(),
        'completed_tasks': user_tasks.filter(is_completed=True).count(),
        'pending_tasks': user_tasks.filter(is_completed=False).count(),
        'overdue_tasks': user_tasks.filter(
            due_date__lt=now,
            is_completed=False
        ).count(),
        'due_today': user_tasks.filter(
            due_date__date=now.date(),
            is_completed=False
        ).count(),
        'high_priority_pending': user_tasks.filter(
            priority='HIGH',
            is_completed=False
        ).count(),
    }
    
    # Calculate completion rate
    if stats['total_tasks'] > 0:
        stats['completion_rate'] = round(
            (stats['completed_tasks'] / stats['total_tasks'] * 100), 1
        )
    else:
        stats['completion_rate'] = 0
    
    return JsonResponse(stats)


# Registration view for web interface
def register_view(request):
    """
    User registration view
    """
    if request.user.is_authenticated:
        return redirect('task:dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'page_title': 'Register'
    }
    return render(request, 'registration/register.html', context)
