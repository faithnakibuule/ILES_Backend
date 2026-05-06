# Apply any outstanding database migrations
python manage.py migrate

# Create a superuser if the environment variable is set
if [[ $CREATE_SUPERUSER ]];
then
  python manage.py createsuperuser --no-input
fi   