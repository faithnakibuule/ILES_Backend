from django.core.management.base import BaseCommand

from reviews.services import ensure_default_evaluation_criteria


class Command(BaseCommand):
    help = "Seeds the default evaluation criteria into the database"

    def handle(self, *args, **kwargs):
        ensure_default_evaluation_criteria()
        self.stdout.write(self.style.SUCCESS("Done! Evaluation criteria are ready."))
