from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.conf import settings
from datetime import date


class Command(BaseCommand):
    help = 'Audit query counts for key endpoints'

    def handle(self, *args, **kwargs):
        settings.DEBUG = True

        from django.contrib.auth import get_user_model
        from logbook.models import WeeklyLog
        from placements.models import InternshipPlacement
        from reviews.models import Evaluation, EvaluationCriteria

        User = get_user_model()

        self.stdout.write("Setting up test data...")

        # Create users
        supervisor = User.objects.create_user(
            email='perf_sup@test.com',
            password='test', role='workplace_supervisor'
        )
        academic = User.objects.create_user(
            email='perf_acad@test.com',
            password='test', role='academic_supervisor'
        )

        # Create 10 students with placements and logs
        students = []
        placements = []
        for i in range(10):
            student = User.objects.create_user(
                email=f'perf_student_{i}@test.com',
                password='test',
                role='student'
            )
            students.append(student)

            placement = InternshipPlacement.objects.create(
                student=student,
                workplace_supervisor=supervisor,
                academic_supervisor=academic,
                company_name=f'Company {i}',
                start_date=date(2025, 1, 1),
                end_date=date(2025, 6, 1),
                status='ACTIVE'
            )
            placements.append(placement)

            # Create 3 logs per student
            for week in range(1, 4):
                WeeklyLog.objects.create(
                    intern=student,
                    placement=placement,
                    week_number=week,
                    activities=f'Activities week {week}',
                    learning_points=f'Learning week {week}',
                    status='SUBMITTED'
                )

        # Create evaluation criteria
        criteria = EvaluationCriteria.objects.create(
            name='Technical Skills',
            description='Technical ability',
            max_score=100,
            weight=1.0
        )

        # Create evaluations
        for placement in placements:
            log = WeeklyLog.objects.filter(
                placement=placement, status='SUBMITTED'
            ).first()
            if log:
                Evaluation.objects.create(
                    log=log,
                    academic_supervisor=academic,
                    total_score=75.0,
                    criteria_scores={str(criteria.id): 75},
                    comments='Good work'
                )

        self.stdout.write("Test data created. Running audit...\n")

        # ── AUDIT ──────────────────────────────────────────
        endpoints = [
            (
                "WeeklyLog list — NO optimization",
                lambda: [
                    (log.intern.email, log.placement.company_name)
                    for log in WeeklyLog.objects.all()
                ]
            ),
            (
                "WeeklyLog list — WITH select_related",
                lambda: [
                    (log.intern.email, log.placement.company_name)
                    for log in WeeklyLog.objects.select_related(
                        'intern', 'placement').all()
                ]
            ),
            (
                "InternshipPlacement list — NO optimization",
                lambda: [
                    (p.student.email, p.workplace_supervisor.email)
                    for p in InternshipPlacement.objects.all()
                ]
            ),
            (
                "InternshipPlacement list — WITH select_related",
                lambda: [
                    (p.student.email, p.workplace_supervisor.email)
                    for p in InternshipPlacement.objects.select_related(
                        'student', 'workplace_supervisor',
                        'academic_supervisor').all()
                ]
            ),
            (
                "Evaluation list — NO optimization",
                lambda: [
                    (e.log.intern.email, e.academic_supervisor.email)
                    for e in Evaluation.objects.all()
                ]
            ),
            (
                "Evaluation list — WITH select_related",
                lambda: [
                    (e.log.intern.email, e.academic_supervisor.email)
                    for e in Evaluation.objects.select_related(
                        'log__intern', 'academic_supervisor').all()
                ]
            ),
        ]

        self.stdout.write("========== PERFORMANCE AUDIT ==========\n")

        for name, query_fn in endpoints:
            reset_queries()
            query_fn()
            count = len(connection.queries)
            total_time = sum(float(q['time']) for q in connection.queries)
            self.stdout.write(
                f"{name}\n"
                f"  Queries: {count} | Time: {total_time:.4f}s\n"
            )

        self.stdout.write("=======================================\n")

        # ── CLEANUP ────────────────────────────────────────
        self.stdout.write("\nCleaning up test data...")
        User.objects.filter(email__startswith='perf_').delete()
        self.stdout.write("Done.\n")