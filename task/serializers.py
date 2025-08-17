from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task


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
        ]
        
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
