from django.test import TestCase
from django.contrib.auth.models import User
from payments.models import Payment, AutomaticPaymentTemplate, AutomaticPayment
from todos.models import Todo
from django.core.files.uploadedfile import SimpleUploadedFile
from colivers.models import Coliver
from chapters.models import Chapter

class PaymentTodoTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        
        # Create test chapter
        self.chapter = Chapter.objects.create(
            name='Test Chapter',
            created_by=self.user
        )
        
        # Create test coliver
        self.coliver = Coliver.objects.create(
            user=self.user,
            chapter_name=self.chapter,
            status='active',
            first_name='Test',
            last_name='Coliver',
            email='test@example.com',
            arrival_date='2024-01-01',
            departure_date='2024-01-10'
        )
        
        # Create test payment
        self.payment = Payment.objects.create(
            user=self.user,
            amount=100000,  # $1,000.00
            description='Test Payment',
            status='requested',
            created_by=self.user
        )
        
        # Create test image for proof
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )

    def test_todo_creation_on_proof_submission(self):
        """Test that todo is only created when proof is submitted"""
        # Initially no todos should exist
        self.assertEqual(Todo.objects.filter(reference_id=str(self.payment.id)).count(), 0)
        
        # Submit proof
        self.payment.status = 'proof_submitted'
        self.payment.proof = self.test_image
        self.payment.save()
        
        # Todo should be created
        self.assertEqual(Todo.objects.filter(reference_id=str(self.payment.id)).count(), 1)
        todo = Todo.objects.get(reference_id=str(self.payment.id))
        self.assertEqual(todo.task_type, 'payment_proof_review')
        self.assertEqual(todo.coliver_name, self.user.get_full_name() or self.user.username)

    def test_no_todo_on_initial_creation(self):
        """Test that no todo is created when payment is first created"""
        self.assertEqual(Todo.objects.filter(reference_id=str(self.payment.id)).count(), 0)

    def test_no_todo_for_automatic_payment(self):
        """Test that no todo is created for automatic payments even when proof is submitted"""
        # Create automatic payment template
        template = AutomaticPaymentTemplate.objects.create(
            title='Test Template',
            description_template='Test payment for {coliver_name}',
            amount_type='fixed',
            fixed_amount=100000,
            date_type='arrival_date',
            days_offset=0,
            is_active=True,
            applies_to_all_colivers=True,
            created_by=self.user
        )
        
        # Create automatic payment
        automatic_payment = AutomaticPayment.objects.create(
            payment=self.payment,
            template=template,
            coliver=self.coliver,
            created_by=self.user
        )
        
        # Submit proof
        self.payment.status = 'proof_submitted'
        self.payment.proof = self.test_image
        self.payment.save()
        
        # No todo should be created for automatic payment
        self.assertEqual(Todo.objects.filter(reference_id=str(self.payment.id)).count(), 0)
