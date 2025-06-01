from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Add email addresses to existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username of the user to update',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to set for the user',
        )
        parser.add_argument(
            '--list-users',
            action='store_true',
            help='List all users without email addresses',
        )

    def handle(self, *args, **options):
        if options['list_users']:
            self.list_users_without_email()
        elif options['username'] and options['email']:
            self.update_user_email(options['username'], options['email'])
        else:
            self.stdout.write(self.style.ERROR('Please provide --username and --email, or use --list-users'))

    def list_users_without_email(self):
        users_without_email = User.objects.filter(email='')
        
        if not users_without_email.exists():
            self.stdout.write(self.style.SUCCESS('All users have email addresses!'))
            return

        self.stdout.write(self.style.WARNING(f'Found {users_without_email.count()} users without email:'))
        for user in users_without_email:
            self.stdout.write(f'  - {user.username} (ID: {user.id})')
        
        self.stdout.write('')
        self.stdout.write('To add an email for a user, run:')
        self.stdout.write('python manage.py add_user_emails --username <username> --email <email>')

    def update_user_email(self, username, email):
        try:
            user = User.objects.get(username=username)
            
            # Check if email is already used
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                self.stdout.write(self.style.ERROR(f'Email {email} is already used by another user!'))
                return
            
            user.email = email
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {username} with email {email}')
            )
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} does not exist!')) 