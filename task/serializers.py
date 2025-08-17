from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Category


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model with all fields
    """
    user = serializers.StringRelatedField(read_only=True)
    is_overdue = serializers.ReadOnlyField()
    days_until_due = serializers.ReadOnlyField()
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'due_date',
            'priority',
            'category',
            'is_completed',
            'user',
            'created_at',
            'updated_at',
            'completed_at',
            'is_overdue',
            'days_until_due',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'completed_at']


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new tasks
    """
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'due_date',
            'priority',
            'category',
            'custom_category',
        ]
    
    def validate(self, attrs):
        """
        Validate that only one category type is provided
        """
        category = attrs.get('category')
        custom_category = attrs.get('custom_category')
        
        # Ensure custom category belongs to the user
        if custom_category and custom_category.user != self.context['request'].user:
            raise serializers.ValidationError({
                'custom_category': 'You can only use your own custom categories.'
            })
        
        return attrs
        
    def validate_title(self, value):
        """
        Validate that title is not empty
        """
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating tasks
    """
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'due_date',
            'priority',
            'category',
            'is_completed',
        ]
        
    def validate_title(self, value):
        """
        Validate that title is not empty
        """
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()


class TaskListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing tasks
    """
    user = serializers.StringRelatedField(read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'due_date',
            'priority',
            'category',
            'is_completed',
            'user',
            'created_at',
            'is_overdue',
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for retrieving single task
    """
    user = serializers.StringRelatedField(read_only=True)
    is_overdue = serializers.ReadOnlyField()
    days_until_due = serializers.ReadOnlyField()
    effective_category = serializers.ReadOnlyField()
    custom_category = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'due_date',
            'priority',
            'category',
            'custom_category',
            'effective_category',
            'is_completed',
            'user',
            'created_at',
            'updated_at',
            'completed_at',
            'is_overdue',
            'days_until_due',
        ]


# Category Serializers
class CategorySerializer(serializers.ModelSerializer):
    """
    Basic serializer for Category model
    """
    user = serializers.StringRelatedField(read_only=True)
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'color',
            'description',
            'user',
            'task_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_task_count(self, obj):
        """Get the number of tasks in this category"""
        return obj.task_set.count()


class CategoryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating custom categories
    """
    class Meta:
        model = Category
        fields = [
            'name',
            'color',
            'description',
        ]
    
    def validate_name(self, value):
        """
        Validate category name
        """
        if not value.strip():
            raise serializers.ValidationError("Category name cannot be empty.")
        
        # Check if user already has a category with this name
        user = self.context['request'].user
        if Category.objects.filter(user=user, name__iexact=value.strip()).exists():
            raise serializers.ValidationError("You already have a category with this name.")
        
        return value.strip().title()
    
    def validate_color(self, value):
        """
        Validate color format (hex)
        """
        if value and not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError("Color must be in hex format (e.g., #007BFF).")
        return value


class CategoryUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating custom categories
    """
    class Meta:
        model = Category
        fields = [
            'name',
            'color',
            'description',
        ]
    
    def validate_name(self, value):
        """
        Validate category name for updates
        """
        if not value.strip():
            raise serializers.ValidationError("Category name cannot be empty.")
        
        # Check if user already has another category with this name
        user = self.context['request'].user
        existing = Category.objects.filter(
            user=user, 
            name__iexact=value.strip()
        ).exclude(id=self.instance.id)
        
        if existing.exists():
            raise serializers.ValidationError("You already have a category with this name.")
        
        return value.strip().title()
    
    def validate_color(self, value):
        """
        Validate color format (hex)
        """
        if value and not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError("Color must be in hex format (e.g., #007BFF).")
        return value


class CategoryListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing categories
    """
    task_count = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    pending_tasks = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'color',
            'description',
            'task_count',
            'completed_tasks',
            'pending_tasks',
            'created_at',
        ]
    
    def get_task_count(self, obj):
        return obj.task_set.count()
    
    def get_completed_tasks(self, obj):
        return obj.task_set.filter(is_completed=True).count()
    
    def get_pending_tasks(self, obj):
        return obj.task_set.filter(is_completed=False).count()
