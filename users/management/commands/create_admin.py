import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates the default admin user if needed, or syncs their password from env vars'

    def handle(self, *args, **kwargs):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@iles.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin!1234')

        existing = User.objects.filter(email=email).first()

        if existing:
            # Sync password and ensure flags are correct in case of prior misconfiguration
            existing.set_password(password)
            existing.is_active = True
            existing.is_staff = True
            existing.is_superuser = True
            existing.role = 'admin'
            existing.save(update_fields=['password', 'is_active', 'is_staff', 'is_superuser', 'role'])
            self.stdout.write(self.style.SUCCESS(
                f'Admin user {email} updated (password synced from env).'
            ))
        else:
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
