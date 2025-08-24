from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task

class TaskForm(forms.ModelForm):
    """Form for creating and editing tasks."""
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title...',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter task description...'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'title': 'Task Title',
            'description': 'Description',
            'due_date': 'Due Date & Time',
            'priority': 'Priority Level',
            'category': 'Category'
        }
        help_texts = {
            'title': 'Give your task a clear, descriptive title',
            'description': 'Add any additional details or notes about this task',
            'due_date': 'When is this task due? Include date and time (Optional)',
            'priority': 'How important is this task?',
            'category': 'What type of task is this?'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes and attributes
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': field.widget.attrs.get('class', '') + ' form-control'})
        
        # Make title required with better validation
        self.fields['title'].required = True
        self.fields['title'].widget.attrs['maxlength'] = 200
        
        # Set default priority if creating new task
        if not self.instance.pk:
            self.fields['priority'].initial = 'MEDIUM'
            self.fields['category'].initial = 'PERSONAL'

    def clean_title(self):
        """Validate task title."""
        title = self.cleaned_data.get('title')
        if title:
            title = title.strip()
            if len(title) < 3:
                raise forms.ValidationError('Task title must be at least 3 characters long.')
            if len(title) > 200:
                raise forms.ValidationError('Task title cannot exceed 200 characters.')
        return title

    def clean(self):
        """Validate the entire form."""
        cleaned_data = super().clean()
        return cleaned_data


class TaskFilterForm(forms.Form):
    """Form for filtering tasks in the list view."""
    
    STATUS_CHOICES = [
        ('', 'All'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    
    PRIORITY_CHOICES = [
        ('', 'All'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search tasks...'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    category = forms.ChoiceField(
        choices=[('', 'All')] + Task.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class QuickTaskForm(forms.ModelForm):
    """Simplified form for quick task creation."""
    
    class Meta:
        model = Task
        fields = ['title', 'priority', 'category', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What needs to be done?',
                'required': True
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['priority'].initial = 'MEDIUM'
        self.fields['category'].initial = 'PERSONAL'


class BulkTaskForm(forms.Form):
    """Form for bulk operations on tasks."""
    
    task_ids = forms.CharField(widget=forms.HiddenInput())
    action = forms.ChoiceField(
        choices=[
            ('complete', 'Mark as Complete'),
            ('incomplete', 'Mark as Incomplete'),
            ('delete', 'Delete'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean_task_ids(self):
        """Validate task IDs."""
        task_ids = self.cleaned_data.get('task_ids')
        if task_ids:
            try:
                return [int(id.strip()) for id in task_ids.split(',') if id.strip()]
            except ValueError:
                raise forms.ValidationError('Invalid task IDs provided.')
        return []


class CustomUserCreationForm(UserCreationForm):
    """Enhanced user registration form."""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Update password field widgets
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter a secure password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

    def save(self, commit=True):
        """Save the user with additional fields."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user
