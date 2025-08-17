from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'priority', 'category', 'is_completed',
        'due_date', 'created_at', 'is_overdue'
    ]
    list_filter = [
        'priority', 'category', 'is_completed', 'created_at', 'due_date'
    ]
    search_fields = ['title', 'description', 'user__username']
    list_editable = ['is_completed', 'priority', 'category']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'is_overdue', 'days_until_due']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'user')
        }),
        ('Task Details', {
            'fields': ('priority', 'category', 'due_date', 'is_completed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Computed Fields', {
            'fields': ('is_overdue', 'days_until_due'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
