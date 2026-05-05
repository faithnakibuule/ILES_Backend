from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from logbook.models import WeeklyLog
from logbook.services import finalize_expired_logs, get_week_number_for_date
from placements.models import InternshipPlacement

User = get_user_model()


@override_settings(TIME_ZONE="UTC", USE_TZ=True)
class StudentWeeklyLogbookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            email="student1@test.com",
            password="testpass123",
            role="student",
        )
        self.supervisor = User.objects.create_user(
            email="supervisor1@test.com",
            password="testpass123",
            role="workplace_supervisor",
        )
        today = timezone.localdate()
        self.placement = InternshipPlacement.objects.create(
            student=self.student,
            workplace_supervisor=self.supervisor,
            company_name="Test Company Ltd",
            start_date=today - timedelta(days=3),
            end_date=today + timedelta(days=60),
            status="ACTIVE",
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.student)

    def test_student_creates_draft_without_sending_placement_or_week(self):
        self.authenticate()

        response = self.client.post(
            "/api/logbook/logs/",
            {
                "activities": "Worked on onboarding flows.",
                "learning_points": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        log = WeeklyLog.objects.get()
        self.assertEqual(log.intern, self.student)
        self.assertEqual(log.placement, self.placement)
        self.assertEqual(log.week_number, 1)
        self.assertEqual(log.status, "DRAFT")

    def test_student_can_submit_when_required_fields_are_complete(self):
        self.authenticate()

        response = self.client.post(
            "/api/logbook/logs/",
            {
                "activities": "Worked on deployment tasks.",
                "learning_points": "Learned release process.",
                "status": "SUBMITTED",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        log = WeeklyLog.objects.get()
        self.assertEqual(log.status, "SUBMITTED")
        self.assertIsNotNone(log.submitted_at)

    def test_student_cannot_submit_with_missing_required_fields(self):
        self.authenticate()

        response = self.client.post(
            "/api/logbook/logs/",
            {
                "activities": "Worked on deployment tasks.",
                "learning_points": "",
                "status": "SUBMITTED",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(WeeklyLog.objects.count(), 1)
        self.assertEqual(WeeklyLog.objects.get().status, "DRAFT")

    def test_student_cannot_create_second_log_for_same_current_week(self):
        self.authenticate()
        self.client.post(
            "/api/logbook/logs/",
            {"activities": "First draft."},
            format="json",
        )

        response = self.client.post(
            "/api/logbook/logs/",
            {"activities": "Second draft."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(WeeklyLog.objects.count(), 1)

    def test_no_active_placement_blocks_form_access(self):
        self.placement.status = "COMPLETED"
        self.placement.save(update_fields=["status"])
        self.authenticate()

        create_response = self.client.post(
            "/api/logbook/logs/",
            {"activities": "Should not save."},
            format="json",
        )
        summary_response = self.client.get("/api/logbook/logs/summary/")

        self.assertEqual(create_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(summary_response.status_code, status.HTTP_200_OK)
        self.assertFalse(summary_response.data["has_active_placement"])

    def test_expired_complete_draft_is_auto_submitted(self):
        placement = InternshipPlacement.objects.create(
            student=self.student,
            workplace_supervisor=self.supervisor,
            company_name="Old Placement",
            start_date=timezone.localdate() - timedelta(days=20),
            end_date=timezone.localdate() + timedelta(days=40),
            status="ACTIVE",
        )
        week_number = get_week_number_for_date(placement, placement.start_date + timedelta(days=1))
        log = WeeklyLog.objects.create(
            intern=self.student,
            placement=placement,
            week_number=week_number,
            activities="Completed all assigned tasks.",
            learning_points="Learned documentation workflows.",
            status="DRAFT",
        )

        finalize_expired_logs(
            now=timezone.make_aware(
                datetime.combine(placement.start_date + timedelta(days=7), time.min)
            )
        )

        log.refresh_from_db()
        self.assertEqual(log.status, "SUBMITTED")
        self.assertIsNotNone(log.submitted_at)

    def test_expired_incomplete_draft_is_marked_missed(self):
        placement = InternshipPlacement.objects.create(
            student=self.student,
            workplace_supervisor=self.supervisor,
            company_name="Old Placement",
            start_date=timezone.localdate() - timedelta(days=20),
            end_date=timezone.localdate() + timedelta(days=40),
            status="ACTIVE",
        )
        log = WeeklyLog.objects.create(
            intern=self.student,
            placement=placement,
            week_number=1,
            activities="",
            learning_points="",
            status="DRAFT",
        )

        finalize_expired_logs(
            now=timezone.make_aware(
                datetime.combine(placement.start_date + timedelta(days=7), time.min)
            )
        )

        log.refresh_from_db()
        self.assertEqual(log.status, "MISSED")

    def test_student_summary_reports_missed_previous_weeks(self):
        self.placement.start_date = timezone.localdate() - timedelta(days=15)
        self.placement.save(update_fields=["start_date"])
        WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=2,
            activities="Week 2 work",
            learning_points="Week 2 learning",
            status="SUBMITTED",
            submitted_at=timezone.now(),
        )
        self.authenticate()

        response = self.client.get("/api/logbook/logs/summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_week"], 3)
        self.assertEqual(response.data["missed_weeks"], [1])
