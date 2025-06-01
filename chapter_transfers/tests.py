from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, date, time
from chapters.models import Chapter
from colivers.models import Coliver
from todos.models import Todo
from .models import ChapterTransferRequest


class ChapterTransferTodoTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        
        # Create test chapters
        self.current_chapter = Chapter.objects.create(
            name='Current Chapter',
            description='Current chapter description'
        )
        self.requested_chapter = Chapter.objects.create(
            name='Requested Chapter', 
            description='Requested chapter description'
        )
        
        # Create coliver profile
        self.coliver = Coliver.objects.create(
            user=self.user,
            chapter_name=self.current_chapter,
            is_active=True
        )
    
    def test_todo_due_date_set_to_start_date(self):
        """Test that todo task due date is set to the start_date from room swap form"""
        # Set up test dates
        start_date = date(2024, 6, 15)  # The date that should become the due date
        end_date = date(2024, 6, 10)    # End date at current chapter
        
        # Create a transfer request
        transfer_request = ChapterTransferRequest.objects.create(
            coliver=self.user,
            current_chapter=self.current_chapter,
            requested_chapter=self.requested_chapter,
            start_date=start_date,
            end_date=end_date,
            reason='Test transfer reason',
            status='pending',
            acknowledgment=True
        )
        
        # Check that a todo was created
        todo = Todo.objects.filter(
            task_type='transfer_review',
            reference_id=str(transfer_request.id)
        ).first()
        
        self.assertIsNotNone(todo, "Todo task should be created for transfer request")
        
        # Check that the due date is set correctly
        expected_due_datetime = timezone.make_aware(
            datetime.combine(start_date, time(23, 59, 59))
        )
        
        self.assertEqual(
            todo.due_date, 
            expected_due_datetime,
            f"Todo due date should be set to start_date ({start_date}) at end of day"
        )
        
        # Verify other todo fields
        self.assertEqual(todo.coliver_name, 'Test User')
        self.assertEqual(todo.status, 'pending')
        self.assertIn('Test User', todo.title)
        self.assertIn('Current Chapter', todo.description)
        self.assertIn('Requested Chapter', todo.description)
    
    def test_admin_todo_due_date_when_approved(self):
        """Test that admin todo also gets due date when transfer is approved"""
        start_date = date(2024, 6, 20)
        end_date = date(2024, 6, 15)
        
        # Create and approve a transfer request
        transfer_request = ChapterTransferRequest.objects.create(
            coliver=self.user,
            current_chapter=self.current_chapter,
            requested_chapter=self.requested_chapter,
            start_date=start_date,
            end_date=end_date,
            reason='Test transfer reason',
            status='pending',
            acknowledgment=True
        )
        
        # Approve the transfer (this should create admin todo)
        transfer_request.status = 'approved'
        transfer_request.save()
        
        # Check that admin todo was created with correct due date
        admin_todo = Todo.objects.filter(
            task_type='transfer_review',
            reference_id=f"{transfer_request.id}_admin"
        ).first()
        
        self.assertIsNotNone(admin_todo, "Admin todo should be created when transfer is approved")
        
        expected_due_datetime = timezone.make_aware(
            datetime.combine(start_date, time(23, 59, 59))
        )
        
        self.assertEqual(
            admin_todo.due_date,
            expected_due_datetime,
            f"Admin todo due date should be set to start_date ({start_date}) at end of day"
        )
        
        self.assertIn('Process chapter transfer', admin_todo.title)
    
    def test_todo_without_start_date(self):
        """Test that todo is created even if start_date is None"""
        # Create transfer request without start_date
        transfer_request = ChapterTransferRequest.objects.create(
            coliver=self.user,
            current_chapter=self.current_chapter,
            requested_chapter=self.requested_chapter,
            start_date=None,  # No start date
            end_date=date(2024, 6, 10),
            reason='Test transfer reason',
            status='pending',
            acknowledgment=True
        )
        
        # Check that todo was still created
        todo = Todo.objects.filter(
            task_type='transfer_review',
            reference_id=str(transfer_request.id)
        ).first()
        
        self.assertIsNotNone(todo, "Todo should be created even without start_date")
        self.assertIsNone(todo.due_date, "Due date should be None when start_date is None")
