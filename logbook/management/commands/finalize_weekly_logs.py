from django.core.management.base import BaseCommand

from logbook.services import finalize_expired_logs


class Command(BaseCommand):
    help = "Auto-submit complete draft weekly logs and mark incomplete ones as missed."

    def handle(self, *args, **options):
        processed = finalize_expired_logs()
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {len(processed)} expired weekly log(s)."
            )
        )
