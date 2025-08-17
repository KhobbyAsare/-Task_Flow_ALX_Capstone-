from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Task(models.Model):
    """
    Task model for task management system
    """
    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]
    
    CATEGORY_CHOICES = [
        ('WORK', 'Work'),
        ('PERSONAL', 'Personal'),
        ('SHOPPING', 'Shopping'),
        ('HEALTH', 'Health'),
        ('EDUCATION', 'Education'),
        ('FINANCE', 'Finance'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=200, help_text="Task title")
    description = models.TextField(blank=True, null=True, help_text="Task description")
    due_date = models.DateTimeField(blank=True, null=True, help_text="Task due date")
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM',
        help_text="Task priority level"
    )
    category = models.CharField(
        max_length=15,
        choices=CATEGORY_CHOICES,
        default='OTHER',
        help_text="Task category"
    )
    is_completed = models.BooleanField(default=False, help_text="Task completion status")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text="User who created this task"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        """Override save to set completed_at timestamp"""
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and not self.is_completed:
            return timezone.now() > self.due_date
        return False
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if self.due_date:
            delta = self.due_date - timezone.now()
            return delta.days
        return None
