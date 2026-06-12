# users/management/commands/reset_admin.py
# One-time command to reset admin password
# DELETE THIS FILE after running

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Resets admin password'

    def handle(self, *args, **kwargs):
        try:
            user = User.objects.get(email='admin@iles.com')
            user.set_password('Admin!1234!')
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.role = 'admin'
            user.save()
            self.stdout.write(self.style.SUCCESS(
                'Admin password reset successfully.'
            ))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Admin user not found.'
            ))