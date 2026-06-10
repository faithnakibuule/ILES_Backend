import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates the default admin user if one does not already exist (idempotent)'

    def handle(self, *args, **kwargs):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@iles.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin!1234')

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
