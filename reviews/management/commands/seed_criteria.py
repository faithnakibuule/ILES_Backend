# reviews/management/commands/seed_criteria.py

from django.core.management.base import BaseCommand
from reviews.models import EvaluationCriteria

class Command(BaseCommand):
    # This text shows when someone runs: python manage.py help seed_criteria
    help = 'Seeds the default evaluation criteria into the database'

    def handle(self, *args, **kwargs):
        # Define the 5 default criteria as a list of dictionaries
        criteria = [
            {
                'name': 'Technical Skills',
                'description': 'Ability to apply technical knowledge on the job',
                'max_score': 100,
                'weight': 0.30,   # 30%
            },
            {
                'name': 'Communication',
                'description': 'Written and verbal communication effectiveness',
                'max_score': 100,
                'weight': 0.20,   # 20%
            },
            {
                'name': 'Punctuality',
                'description': 'Consistency in meeting deadlines and attendance',
                'max_score': 100,
                'weight': 0.15,   # 15%
            },
            {
                'name': 'Initiative',
                'description': 'Proactiveness and willingness to take on tasks',
                'max_score': 100,
                'weight': 0.20,   # 20%
            },
            {
                'name': 'Professionalism',
                'description': 'Conduct, attitude, and workplace behaviour',
                'max_score': 100,
                'weight': 0.15,   # 15%
            },
        ]

        # Loop through each criterion and create it only if it doesn't exist yet
        for item in criteria:
            obj, created = EvaluationCriteria.objects.get_or_create(
                name=item['name'],         # look up by name
                defaults={                 # only set these if creating new
                    'description': item['description'],
                    'max_score':   item['max_score'],
                    'weight':      item['weight'],
                }
            )
            if created:
                # Green success message in terminal
                self.stdout.write(self.style.SUCCESS(f"✅ Created: {obj.name}"))
            else:
                # Yellow warning — already exists, skipped
                self.stdout.write(self.style.WARNING(f"⚠️  Already exists: {obj.name}"))

        self.stdout.write(self.style.SUCCESS('\nDone! Evaluation criteria are ready.'))