# users/management/commands/create_admin.py
# One-time command to create a superuser on production
# DELETE THIS FILE after running it once

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a default superuser for production'

    def handle(self, *args, **kwargs):
        email = 'admin@iles.com'
        password = 'Admin!1234!'
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(
                f'Admin user {email} already exists — skipping.'
            ))
            return

        User.objects.create_superuser(
            email=email,
            password=password,
            first_name='ILES',
            last_name='Admin',
            role='admin',
        )
        self.stdout.write(self.style.SUCCESS(
            f'Superuser {email} created successfully.'
        ))