from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    """
    Custom category model for user-defined task categories
    """
    name = models.CharField(max_length=50, help_text="Category name")
    color = models.CharField(
        max_length=7, 
        blank=True, 
        null=True, 
        help_text="Color code for category (hex format)",
        default="#007BFF"
    )
    description = models.TextField(blank=True, null=True, help_text="Category description")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='custom_categories',
        help_text="User who created this category"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Custom Category'
        verbose_name_plural = 'Custom Categories'
        # Ensure user cannot create duplicate category names
        unique_together = ['name', 'user']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    def clean(self):
        # Convert name to title case for consistency
        if self.name:
            self.name = self.name.title()
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


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
        ('FITNESS', 'Fitness'),
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
    # Default system category (optional)
    category = models.CharField(
        max_length=15,
        choices=CATEGORY_CHOICES,
        blank=True,
        null=True,
        help_text="Default system category"
    )
    # Custom user category (optional)
    custom_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Custom user-defined category"
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
    
    @property
    def effective_category(self):
        """Get the effective category (custom takes precedence over default)"""
        if self.custom_category:
            return {
                'type': 'custom',
                'id': self.custom_category.id,
                'name': self.custom_category.name,
                'color': self.custom_category.color
            }
        elif self.category:
            return {
                'type': 'default',
                'code': self.category,
                'name': dict(self.CATEGORY_CHOICES).get(self.category, self.category)
            }
        else:
            return {
                'type': 'default',
                'code': 'OTHER',
                'name': 'Other'
            }
    
    def clean(self):
        # Ensure at least one category is set (default or custom)
        if not self.category and not self.custom_category:
            self.category = 'OTHER'
