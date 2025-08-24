import json
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from unittest.mock import patch
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


class BaseTaskTestCase(APITestCase):
    """Base test case with common setup for task API tests"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test users
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        # Create tokens
        self.token = Token.objects.create(user=self.test_user)
        self.other_token = Token.objects.create(user=self.other_user)
        
        # Create test categories
        self.test_category = Category.objects.create(
            name='Test Category',
            color='#FF0000',
            description='Test category description',
            user=self.test_user
        )
        
        self.other_category = Category.objects.create(
            name='Other Category',
            color='#00FF00',
            description='Other user category',
            user=self.other_user
        )
        
        # Sample task data
        self.valid_task_data = {
            'title': 'Test Task',
            'description': 'Test task description',
            'due_date': (timezone.now() + timedelta(days=1)).isoformat(),
            'priority': 'HIGH',
            'category': 'WORK'
        }
        
        self.valid_category_data = {
            'name': 'New Category',
            'color': '#0000FF',
            'description': 'New category description'
        }
        
        # Create sample tasks
        self.completed_task = Task.objects.create(
            title='Completed Task',
            description='This is completed',
            priority='MEDIUM',
            category='WORK',
            is_completed=True,
            user=self.test_user,
            completed_at=timezone.now()
        )
        
        self.pending_task = Task.objects.create(
            title='Pending Task',
            description='This is pending',
            priority='HIGH',
            category='PERSONAL',
            due_date=timezone.now() + timedelta(days=1),
            user=self.test_user
        )
        
        self.overdue_task = Task.objects.create(
            title='Overdue Task',
            description='This is overdue',
            priority='LOW',
            category='WORK',
            due_date=timezone.now() - timedelta(days=1),
            user=self.test_user
        )
        
        # Task for other user
        self.other_user_task = Task.objects.create(
            title='Other User Task',
            description='Task for other user',
            priority='MEDIUM',
            category='FITNESS',
            user=self.other_user
        )
    
    def authenticate_user(self, user=None):
        """Helper method to authenticate test user"""
        if user is None:
            self.client.force_authenticate(user=self.test_user, token=self.token)
        else:
            token = self.other_token if user == self.other_user else self.token
            self.client.force_authenticate(user=user, token=token)
    
    def create_test_task(self, user=None, **kwargs):
        """Helper method to create additional test tasks"""
        if user is None:
            user = self.test_user
        
        defaults = {
            'title': 'Helper Task',
            'description': 'Helper task description',
            'priority': 'MEDIUM',
            'category': 'OTHER',
            'user': user
        }
        defaults.update(kwargs)
        return Task.objects.create(**defaults)


class TaskCRUDTests(BaseTaskTestCase):
    """Test cases for Task CRUD operations"""
    
    def test_create_task_success(self):
        """Test successful task creation"""
        self.authenticate_user()
        url = reverse('task:task-create')
        
        response = self.client.post(url, self.valid_task_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('task', response.data)
        self.assertEqual(response.data['message'], 'Task created successfully')
        
        # Verify task was created in database
        self.assertTrue(Task.objects.filter(title='Test Task', user=self.test_user).exists())
        
        task = Task.objects.get(title='Test Task', user=self.test_user)
        self.assertEqual(task.priority, 'HIGH')
        self.assertEqual(task.category, 'WORK')
    
    def test_create_task_with_custom_category(self):
        """Test creating task with custom category"""
        self.authenticate_user()
        url = reverse('task:task-create')
        
        data = self.valid_task_data.copy()
        data.pop('category')  # Remove default category
        data['custom_category'] = self.test_category.id
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get(title='Test Task', user=self.test_user)
        self.assertEqual(task.custom_category, self.test_category)
        self.assertIsNone(task.category)
    
    def test_create_task_with_other_users_category_fails(self):
        """Test creating task with other user's custom category fails"""
        self.authenticate_user()
        url = reverse('task:task-create')
        
        data = self.valid_task_data.copy()
        data['custom_category'] = self.other_category.id  # Other user's category
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('custom_category', response.data)
    
    def test_create_task_missing_title_fails(self):
        """Test creating task without title fails"""
        self.authenticate_user()
        url = reverse('task:task-create')
        
        data = self.valid_task_data.copy()
        data['title'] = '  '  # Empty title
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
    
    def test_create_task_unauthenticated_fails(self):
        """Test creating task without authentication fails"""
        url = reverse('task:task-create')
        
        response = self.client.post(url, self.valid_task_data, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_list_tasks_success(self):
        """Test successful task listing"""
        self.authenticate_user()
        url = reverse('task:task-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle paginated response
        if 'results' in response.data:
            # Paginated response
            task_data = response.data['results']
            self.assertIn('message', task_data)
            self.assertIn('tasks', task_data)
            self.assertEqual(task_data['message'], 'Tasks retrieved successfully')
            tasks = task_data['tasks']
        else:
            # Non-paginated response
            self.assertIn('message', response.data)
            self.assertIn('tasks', response.data)
            tasks = response.data['tasks']
        
        # Should return only user's tasks (3 tasks)
        self.assertEqual(len(tasks), 3)
        task_titles = [task['title'] for task in tasks]
        self.assertIn('Completed Task', task_titles)
        self.assertIn('Pending Task', task_titles)
        self.assertIn('Overdue Task', task_titles)
        self.assertNotIn('Other User Task', task_titles)
    
    def test_list_tasks_with_filters(self):
        """Test task listing with filters"""
        self.authenticate_user()
        url = reverse('task:task-list')
        
        # Filter by priority
        response = self.client.get(url, {'priority': 'HIGH'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle paginated response
        tasks = response.data['results']['tasks'] if 'results' in response.data else response.data['tasks']
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], 'Pending Task')
        
        # Filter by completion status
        response = self.client.get(url, {'is_completed': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        tasks = response.data['results']['tasks'] if 'results' in response.data else response.data['tasks']
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], 'Completed Task')
        
        # Filter by category
        response = self.client.get(url, {'category': 'WORK'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        tasks = response.data['results']['tasks'] if 'results' in response.data else response.data['tasks']
        self.assertEqual(len(tasks), 2)  # Completed and Overdue tasks
    
    def test_list_tasks_with_search(self):
        """Test task listing with search"""
        self.authenticate_user()
        url = reverse('task:task-list')
        
        response = self.client.get(url, {'search': 'pending'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle paginated response
        tasks = response.data['results']['tasks'] if 'results' in response.data else response.data['tasks']
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], 'Pending Task')
    
    def test_retrieve_task_success(self):
        """Test successful task retrieval"""
        self.authenticate_user()
        url = reverse('task:task-detail', kwargs={'id': self.pending_task.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('task', response.data)
        self.assertEqual(response.data['message'], 'Task retrieved successfully')
        self.assertEqual(response.data['task']['title'], 'Pending Task')
        self.assertEqual(response.data['task']['id'], self.pending_task.id)
    
    def test_retrieve_other_users_task_fails(self):
        """Test retrieving other user's task fails"""
        self.authenticate_user()
        url = reverse('task:task-detail', kwargs={'id': self.other_user_task.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_task_success(self):
        """Test successful task update"""
        self.authenticate_user()
        url = reverse('task:task-update', kwargs={'id': self.pending_task.id})
        
        update_data = {
            'title': 'Updated Task Title',
            'priority': 'LOW',
            'is_completed': True
        }
        
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Task updated successfully')
        
        # Verify task was updated
        self.pending_task.refresh_from_db()
        self.assertEqual(self.pending_task.title, 'Updated Task Title')
        self.assertEqual(self.pending_task.priority, 'LOW')
        self.assertTrue(self.pending_task.is_completed)
        self.assertIsNotNone(self.pending_task.completed_at)
    
    def test_update_task_empty_title_fails(self):
        """Test updating task with empty title fails"""
        self.authenticate_user()
        url = reverse('task:task-update', kwargs={'id': self.pending_task.id})
        
        update_data = {'title': '   '}
        
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
    
    def test_delete_task_success(self):
        """Test successful task deletion"""
        self.authenticate_user()
        url = reverse('task:task-delete', kwargs={'id': self.pending_task.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('Pending Task', response.data['message'])
        
        # Verify task was deleted
        self.assertFalse(Task.objects.filter(id=self.pending_task.id).exists())
    
    def test_delete_other_users_task_fails(self):
        """Test deleting other user's task fails"""
        self.authenticate_user()
        url = reverse('task:task-delete', kwargs={'id': self.other_user_task.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Verify task still exists
        self.assertTrue(Task.objects.filter(id=self.other_user_task.id).exists())


class TaskOrganizationTests(BaseTaskTestCase):
    """Test cases for Task organization endpoints"""
    
    def test_get_task_categories(self):
        """Test retrieving task categories with statistics"""
        self.authenticate_user()
        url = reverse('task:task-categories')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('categories', response.data)
        
        # Check that categories have correct structure
        categories = response.data['categories']
        self.assertTrue(len(categories) > 0)
        
        # Find WORK category stats
        work_category = next(cat for cat in categories if cat['code'] == 'WORK')
        self.assertEqual(work_category['total_tasks'], 2)  # Completed + Overdue
        self.assertEqual(work_category['completed_tasks'], 1)
        self.assertEqual(work_category['pending_tasks'], 1)
    
    def test_get_tasks_by_category(self):
        """Test retrieving tasks by specific category"""
        self.authenticate_user()
        url = reverse('task:tasks-by-category', kwargs={'category': 'work'})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('tasks', response.data)
        self.assertIn('category', response.data)
        
        # Should return 2 WORK category tasks
        self.assertEqual(len(response.data['tasks']), 2)
        self.assertEqual(response.data['category']['code'], 'WORK')
        self.assertEqual(response.data['category']['total_tasks'], 2)
    
    def test_get_task_priorities(self):
        """Test retrieving task priorities with statistics"""
        self.authenticate_user()
        url = reverse('task:task-priorities')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('priorities', response.data)
        
        # Check that priorities have correct structure
        priorities = response.data['priorities']
        self.assertEqual(len(priorities), 3)  # HIGH, MEDIUM, LOW
        
        # Find HIGH priority stats
        high_priority = next(p for p in priorities if p['code'] == 'HIGH')
        self.assertEqual(high_priority['total_tasks'], 1)  # Pending task
        self.assertEqual(high_priority['completed_tasks'], 0)
        self.assertEqual(high_priority['pending_tasks'], 1)
    
    def test_get_tasks_by_priority(self):
        """Test retrieving tasks by specific priority"""
        self.authenticate_user()
        url = reverse('task:tasks-by-priority', kwargs={'priority': 'high'})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('tasks', response.data)
        self.assertIn('priority', response.data)
        
        # Should return 1 HIGH priority task
        self.assertEqual(len(response.data['tasks']), 1)
        self.assertEqual(response.data['tasks'][0]['title'], 'Pending Task')
        self.assertEqual(response.data['priority']['code'], 'HIGH')


class TaskStatusTests(BaseTaskTestCase):
    """Test cases for Task status endpoints"""
    
    def test_get_completed_tasks(self):
        """Test retrieving completed tasks"""
        self.authenticate_user()
        url = reverse('task:completed-tasks')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('tasks', response.data)
        self.assertIn('total_completed', response.data)
        
        # Should return 1 completed task
        self.assertEqual(response.data['total_completed'], 1)
        self.assertEqual(len(response.data['tasks']), 1)
        self.assertEqual(response.data['tasks'][0]['title'], 'Completed Task')
        self.assertTrue(response.data['tasks'][0]['is_completed'])
    
    def test_get_pending_tasks(self):
        """Test retrieving pending tasks"""
        self.authenticate_user()
        url = reverse('task:pending-tasks')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('tasks', response.data)
        self.assertIn('total_pending', response.data)
        self.assertIn('overdue_count', response.data)
        
        # Should return 2 pending tasks (Pending + Overdue)
        self.assertEqual(response.data['total_pending'], 2)
        self.assertEqual(response.data['overdue_count'], 1)
        self.assertEqual(len(response.data['tasks']), 2)
    
    def test_get_urgent_tasks(self):
        """Test retrieving urgent tasks (HIGH priority and/or overdue)"""
        self.authenticate_user()
        url = reverse('task:urgent-tasks')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('tasks', response.data)
        self.assertIn('summary', response.data)
        
        # Should return 2 urgent tasks (1 HIGH priority + 1 overdue)
        summary = response.data['summary']
        self.assertEqual(summary['total_urgent'], 2)
        self.assertEqual(summary['high_priority'], 1)
        self.assertEqual(summary['overdue'], 1)
        self.assertEqual(len(response.data['tasks']), 2)
    
    def test_bulk_task_status_update_success(self):
        """Test bulk updating task completion status"""
        self.authenticate_user()
        url = reverse('task:bulk-task-update')
        
        # Create additional tasks
        task1 = self.create_test_task(title='Bulk Task 1')
        task2 = self.create_test_task(title='Bulk Task 2')
        
        data = {
            'task_ids': [task1.id, task2.id],
            'is_completed': True
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('updated_count', response.data)
        self.assertEqual(response.data['updated_count'], 2)
        
        # Verify tasks were updated
        task1.refresh_from_db()
        task2.refresh_from_db()
        self.assertTrue(task1.is_completed)
        self.assertTrue(task2.is_completed)
        self.assertIsNotNone(task1.completed_at)
        self.assertIsNotNone(task2.completed_at)
    
    def test_bulk_task_status_update_missing_task_ids(self):
        """Test bulk update fails with missing task_ids"""
        self.authenticate_user()
        url = reverse('task:bulk-task-update')
        
        data = {'is_completed': True}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('task_ids is required', response.data['error'])
    
    def test_bulk_task_status_update_other_users_tasks(self):
        """Test bulk update with other user's tasks returns not found"""
        self.authenticate_user()
        url = reverse('task:bulk-task-update')
        
        data = {
            'task_ids': [self.other_user_task.id],
            'is_completed': True
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('No valid tasks found', response.data['error'])


class TaskDashboardAndStatsTests(BaseTaskTestCase):
    """Test cases for Task dashboard and statistics endpoints"""
    
    def test_get_task_stats(self):
        """Test retrieving task statistics"""
        self.authenticate_user()
        url = reverse('task:task-stats')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('stats', response.data)
        
        stats = response.data['stats']
        self.assertEqual(stats['total_tasks'], 3)
        self.assertEqual(stats['completed_tasks'], 1)
        self.assertEqual(stats['pending_tasks'], 2)
        self.assertEqual(stats['high_priority_pending'], 1)
        self.assertEqual(stats['overdue_tasks'], 1)
        self.assertIsInstance(stats['completion_rate'], float)
        self.assertIn('categories', stats)
    
    def test_get_task_dashboard(self):
        """Test retrieving comprehensive task dashboard"""
        self.authenticate_user()
        url = reverse('task:task-dashboard')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('dashboard', response.data)
        
        dashboard = response.data['dashboard']
        
        # Check overview section
        self.assertIn('overview', dashboard)
        overview = dashboard['overview']
        self.assertEqual(overview['total_tasks'], 3)
        self.assertEqual(overview['completed_tasks'], 1)
        self.assertEqual(overview['pending_tasks'], 2)
        
        # Check other sections exist
        self.assertIn('priorities', dashboard)
        self.assertIn('categories', dashboard)
        self.assertIn('time_based', dashboard)
        self.assertIn('recent_activity', dashboard)
        self.assertIn('top_categories', dashboard)
        
        # Verify time-based stats
        time_based = dashboard['time_based']
        self.assertEqual(time_based['overdue'], 1)


class TaskModelTests(TestCase):
    """Test cases for Task model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='modeltest',
            email='model@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
    
    def test_task_str_method(self):
        """Test task string representation"""
        task = Task.objects.create(
            title='Test Task',
            user=self.user
        )
        
        expected_str = f"{task.title} - {self.user.username}"
        self.assertEqual(str(task), expected_str)
    
    def test_task_save_sets_completed_at(self):
        """Test that save method sets completed_at when task is completed"""
        task = Task.objects.create(
            title='Test Task',
            user=self.user
        )
        
        # Initially not completed
        self.assertFalse(task.is_completed)
        self.assertIsNone(task.completed_at)
        
        # Complete the task
        task.is_completed = True
        task.save()
        
        self.assertIsNotNone(task.completed_at)
        
        # Mark as incomplete
        task.is_completed = False
        task.save()
        
        self.assertIsNone(task.completed_at)
    
    def test_task_is_overdue_property(self):
        """Test is_overdue property"""
        # Task without due date
        task = Task.objects.create(
            title='No Due Date',
            user=self.user
        )
        self.assertFalse(task.is_overdue)
        
        # Task with future due date
        future_task = Task.objects.create(
            title='Future Task',
            due_date=timezone.now() + timedelta(days=1),
            user=self.user
        )
        self.assertFalse(future_task.is_overdue)
        
        # Task with past due date
        overdue_task = Task.objects.create(
            title='Overdue Task',
            due_date=timezone.now() - timedelta(days=1),
            user=self.user
        )
        self.assertTrue(overdue_task.is_overdue)
        
        # Completed overdue task
        completed_overdue = Task.objects.create(
            title='Completed Overdue',
            due_date=timezone.now() - timedelta(days=1),
            is_completed=True,
            user=self.user
        )
        self.assertFalse(completed_overdue.is_overdue)
    
    def test_task_days_until_due_property(self):
        """Test days_until_due property"""
        # Task without due date
        task = Task.objects.create(
            title='No Due Date',
            user=self.user
        )
        self.assertIsNone(task.days_until_due)
        
        # Task with future due date
        future_date = timezone.now() + timedelta(days=5)
        future_task = Task.objects.create(
            title='Future Task',
            due_date=future_date,
            user=self.user
        )
        self.assertEqual(future_task.days_until_due, 5)
    
    def test_task_effective_category_property(self):
        """Test effective_category property"""
        # Task with custom category
        task_with_custom = Task.objects.create(
            title='Custom Category Task',
            custom_category=self.category,
            user=self.user
        )
        
        effective = task_with_custom.effective_category
        self.assertEqual(effective['type'], 'custom')
        self.assertEqual(effective['name'], 'Test Category')
        self.assertEqual(effective['id'], self.category.id)
        
        # Task with default category
        task_with_default = Task.objects.create(
            title='Default Category Task',
            category='WORK',
            user=self.user
        )
        
        effective = task_with_default.effective_category
        self.assertEqual(effective['type'], 'default')
        self.assertEqual(effective['code'], 'WORK')
        self.assertEqual(effective['name'], 'Work')
        
        # Task with no category (should default to OTHER)
        task_no_category = Task.objects.create(
            title='No Category Task',
            user=self.user
        )
        
        effective = task_no_category.effective_category
        self.assertEqual(effective['type'], 'default')
        self.assertEqual(effective['code'], 'OTHER')
        self.assertEqual(effective['name'], 'Other')
    
    def test_task_clean_method_sets_default_category(self):
        """Test clean method sets default category when none provided"""
        task = Task(
            title='Test Task',
            user=self.user
        )
        task.clean()
        
        self.assertEqual(task.category, 'OTHER')


class CategoryModelTests(TestCase):
    """Test cases for Category model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='categorytest',
            email='category@example.com',
            password='testpass123'
        )
    
    def test_category_str_method(self):
        """Test category string representation"""
        category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        
        expected_str = f"{category.name} - {self.user.username}"
        self.assertEqual(str(category), expected_str)
    
    def test_category_clean_method_title_cases_name(self):
        """Test clean method converts name to title case"""
        category = Category(
            name='test category',
            user=self.user
        )
        category.clean()
        
        self.assertEqual(category.name, 'Test Category')
    
    def test_category_save_calls_clean(self):
        """Test save method calls clean"""
        category = Category.objects.create(
            name='lowercase category',
            user=self.user
        )
        
        self.assertEqual(category.name, 'Lowercase Category')
    
    def test_category_unique_together_constraint(self):
        """Test unique_together constraint for name and user"""
        # Create first category
        Category.objects.create(
            name='Duplicate Name',
            user=self.user
        )
        
        # Try to create duplicate for same user
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Category.objects.create(
                name='Duplicate Name',
                user=self.user
            )
    
    def test_category_default_color(self):
        """Test category default color"""
        category = Category.objects.create(
            name='Default Color Category',
            user=self.user
        )
        
        self.assertEqual(category.color, '#007BFF')


class TaskSerializerTests(TestCase):
    """Test cases for Task serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='serializertest',
            email='serializer@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
    
    def test_task_create_serializer_valid_data(self):
        """Test TaskCreateSerializer with valid data"""
        data = {
            'title': 'Test Task',
            'description': 'Test description',
            'priority': 'HIGH',
            'category': 'WORK'
        }
        
        # Mock request context
        from unittest.mock import Mock
        request = Mock()
        request.user = self.user
        
        serializer = TaskCreateSerializer(
            data=data, 
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        task = serializer.save(user=self.user)
        
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.priority, 'HIGH')
        self.assertEqual(task.category, 'WORK')
        self.assertEqual(task.user, self.user)
    
    def test_task_create_serializer_invalid_empty_title(self):
        """Test TaskCreateSerializer with empty title"""
        data = {
            'title': '   ',
            'priority': 'HIGH'
        }
        
        serializer = TaskCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
    
    def test_task_create_serializer_other_users_custom_category(self):
        """Test TaskCreateSerializer with other user's custom category"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_category = Category.objects.create(
            name='Other Category',
            user=other_user
        )
        
        data = {
            'title': 'Test Task',
            'custom_category': other_category.id
        }
        
        from unittest.mock import Mock
        request = Mock()
        request.user = self.user
        
        serializer = TaskCreateSerializer(
            data=data, 
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('custom_category', serializer.errors)


class CategorySerializerTests(TestCase):
    """Test cases for Category serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='categorysertest',
            email='catser@example.com',
            password='testpass123'
        )
    
    def test_category_create_serializer_valid_data(self):
        """Test CategoryCreateSerializer with valid data"""
        data = {
            'name': 'test category',
            'color': '#FF0000',
            'description': 'Test description'
        }
        
        from unittest.mock import Mock
        request = Mock()
        request.user = self.user
        
        serializer = CategoryCreateSerializer(
            data=data, 
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        category = serializer.save(user=self.user)
        
        self.assertEqual(category.name, 'Test Category')  # Title cased
        self.assertEqual(category.color, '#FF0000')
        self.assertEqual(category.user, self.user)
    
    def test_category_create_serializer_duplicate_name(self):
        """Test CategoryCreateSerializer with duplicate name"""
        # Create existing category
        Category.objects.create(
            name='Existing Category',
            user=self.user
        )
        
        data = {
            'name': 'existing category',  # Same name, different case
        }
        
        from unittest.mock import Mock
        request = Mock()
        request.user = self.user
        
        serializer = CategoryCreateSerializer(
            data=data, 
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_category_create_serializer_invalid_color(self):
        """Test CategoryCreateSerializer with invalid color format"""
        data = {
            'name': 'Test Category',
            'color': 'not-a-hex-color'
        }
        
        from unittest.mock import Mock
        request = Mock()
        request.user = self.user
        
        serializer = CategoryCreateSerializer(
            data=data, 
            context={'request': request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('color', serializer.errors)
