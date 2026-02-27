import os

from django.core.wsgi import get_wsgi_application

# This points Django to your settings file
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# This is the specific attribute the error was looking for!
application = get_wsgi_application()