# Apply any outstanding database migrations
python manage.py migrate

# Create the admin user if it doesn't exist yet (idempotent — safe on every deploy)
python manage.py create_admin