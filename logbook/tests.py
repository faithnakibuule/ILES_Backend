#from django.test import TestCase

# Create your tests here.

# logbook/tests.py
# Tests for the WeeklyLog model and API endpoints.
# Covers: creating logs, unique constraint, supervisor access, status transitions.

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from logbook.models import WeeklyLog
from placements.models import InternshipPlacement

User = get_user_model()  # Gets your CustomUser model


# ══════════════════════════════════════════════════════════════════════════════
# Helper: setUp is called before EVERY test method in a class.
# We create all the users and data we need here so each test starts clean.
# ══════════════════════════════════════════════════════════════════════════════

class LogbookTestCase(TestCase):
    """Base test case with shared setup for all logbook tests."""

    def setUp(self):
        # Create an API client — this is what makes fake HTTP requests
        self.client = APIClient()

        # ── Create test users ──────────────────────────────────────────────
        # Student 1 — the main student we test with
        self.student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            role='student',
        )

        # Student 2 — used to test that students can't see each other's logs
        self.student2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123',
            role='student',
        )

        # Workplace supervisor — assigned to student 1
        self.supervisor = User.objects.create_user(
            username='supervisor1',
            email='supervisor1@test.com',
            password='testpass123',
            role='workplace_supervisor',
        )

        # A different supervisor — not assigned to anyone in our tests
        self.other_supervisor = User.objects.create_user(
            username='supervisor2',
            email='supervisor2@test.com',
            password='testpass123',
            role='workplace_supervisor',
        )

        # ── Create test placements ─────────────────────────────────────────
        # Student 1's placement — assigned to supervisor 1
        self.placement = InternshipPlacement.objects.create(
            student=self.student,
            workplace_supervisor=self.supervisor,
            company_name='Test Company Ltd',
            start_date='2025-01-01',
            end_date='2025-06-30',
            status='ACTIVE',
        )

        # Student 2's placement — also assigned to supervisor 1
        self.placement2 = InternshipPlacement.objects.create(
            student=self.student2,
            workplace_supervisor=self.supervisor,
            company_name='Another Company',
            start_date='2025-01-01',
            end_date='2025-06-30',
            status='ACTIVE',
        )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: Student can create a DRAFT log
# ══════════════════════════════════════════════════════════════════════════════

class TestStudentCreateDraftLog(LogbookTestCase):

    def test_student_can_create_draft_log(self):
        """
        A logged-in student should be able to POST a new log
        with status DRAFT and get a 201 Created response.
        """
        # Log in as student 1
        # force_authenticate skips the JWT login step — simulates a logged-in user
        self.client.force_authenticate(user=self.student)

        # Data to send — like filling in the LogFormPage form
        data = {
            'week_number':     1,
            'activities':      'I worked on the authentication module this week.',
            'learning_points': 'I learned how JWT tokens are structured and validated.',
            'placement':       self.placement.id,
            'status':          'DRAFT',
        }

        # Make the POST request to create the log
        response = self.client.post('/api/logs/', data, format='json')

        # ── Assertions ────────────────────────────────────────────────────
        # 201 = Created — the log was successfully saved
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            f'Expected 201 but got {response.status_code}. Response: {response.data}'
        )

        # Confirm the log was actually saved in the database
        self.assertEqual(WeeklyLog.objects.count(), 1)

        # Confirm the status is DRAFT
        log = WeeklyLog.objects.first()
        self.assertEqual(log.status, 'DRAFT')

        # Confirm it belongs to the right student
        self.assertEqual(log.intern, self.student)

    def test_unauthenticated_user_cannot_create_log(self):
        """
        A user without a token should get 401 Unauthorized.
        This ensures the endpoint is protected.
        """
        # No force_authenticate — simulates a logged-out user
        data = {
            'week_number':     1,
            'activities':      'Some activities.',
            'learning_points': 'Some learning.',
            'placement':       self.placement.id,
        }

        response = self.client.post('/api/logs/', data, format='json')

        # 401 = Unauthorized — correct, not logged in
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Student cannot submit twice for the same week (unique_together)
# ══════════════════════════════════════════════════════════════════════════════

class TestUniqueTogetherConstraint(LogbookTestCase):

    def test_student_cannot_create_duplicate_log_for_same_week(self):
        """
        The WeeklyLog model has unique_together = [['intern', 'week_number']].
        A student trying to create a second log for the same week
        should get a 400 Bad Request response.
        """
        self.client.force_authenticate(user=self.student)

        data = {
            'week_number':     2,
            'activities':      'First log for week 2.',
            'learning_points': 'First learning for week 2.',
            'placement':       self.placement.id,
            'status':          'DRAFT',
        }

        # First submission — should succeed
        first_response = self.client.post('/api/logs/', data, format='json')
        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
            'First log creation should succeed.'
        )

        # Second submission for the SAME week — should fail
        duplicate_data = {
            'week_number':     2,  # same week number!
            'activities':      'Trying to submit again for week 2.',
            'learning_points': 'Duplicate learning points.',
            'placement':       self.placement.id,
            'status':          'DRAFT',
        }

        second_response = self.client.post('/api/logs/', duplicate_data, format='json')

        # 400 = Bad Request — Django enforces unique_together at the API level
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'Duplicate log for same week should return 400.'
        )

        # Only 1 log should exist in the database — the duplicate was rejected
        self.assertEqual(WeeklyLog.objects.count(), 1)

    def test_student_can_create_logs_for_different_weeks(self):
        """
        Creating logs for week 1 and week 2 should both succeed
        since they are different weeks.
        """
        self.client.force_authenticate(user=self.student)

        # Week 1 log
        self.client.post('/api/logs/', {
            'week_number': 1, 'activities': 'Week 1 activities.',
            'learning_points': 'Week 1 learning.', 'placement': self.placement.id,
        }, format='json')

        # Week 2 log — different week, should succeed
        response = self.client.post('/api/logs/', {
            'week_number': 2, 'activities': 'Week 2 activities.',
            'learning_points': 'Week 2 learning.', 'placement': self.placement.id,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WeeklyLog.objects.count(), 2)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: Workplace supervisor can only see their own interns' logs
# ══════════════════════════════════════════════════════════════════════════════

class TestSupervisorLogAccess(LogbookTestCase):

    def setUp(self):
        super().setUp()  # Run parent setUp first to create users and placements

        # Create a log for student 1 (assigned to supervisor 1)
        self.log_student1 = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=1,
            activities='Student 1 week 1 activities.',
            learning_points='Student 1 week 1 learning.',
            status='SUBMITTED',
        )

        # Create a log for student 2 (also assigned to supervisor 1)
        self.log_student2 = WeeklyLog.objects.create(
            intern=self.student2,
            placement=self.placement2,
            week_number=1,
            activities='Student 2 week 1 activities.',
            learning_points='Student 2 week 1 learning.',
            status='SUBMITTED',
        )

        # Create a placement for a student under the OTHER supervisor
        self.other_student = User.objects.create_user(
            username='student3',
            email='student3@test.com',
            password='testpass123',
            role='student',
        )
        self.other_placement = InternshipPlacement.objects.create(
            student=self.other_student,
            workplace_supervisor=self.other_supervisor,
            company_name='Other Company',
            start_date='2025-01-01',
            end_date='2025-06-30',
            status='ACTIVE',
        )
        # Log belonging to a student under a DIFFERENT supervisor
        self.log_other = WeeklyLog.objects.create(
            intern=self.other_student,
            placement=self.other_placement,
            week_number=1,
            activities='Other student activities.',
            learning_points='Other student learning.',
            status='SUBMITTED',
        )

    def test_supervisor_sees_only_their_interns_logs(self):
        """
        Supervisor 1 is assigned to student1 and student2.
        They should see logs from both students but NOT from other_student
        who is assigned to supervisor 2.
        """
        self.client.force_authenticate(user=self.supervisor)

        response = self.client.get('/api/logs/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Extract the log IDs from the response
        returned_ids = [log['id'] for log in response.data]

        # Should see student1 and student2 logs
        self.assertIn(
            self.log_student1.id, returned_ids,
            'Supervisor should see their intern student1 log.'
        )
        self.assertIn(
            self.log_student2.id, returned_ids,
            'Supervisor should see their intern student2 log.'
        )

        # Should NOT see the log from a student under a different supervisor
        self.assertNotIn(
            self.log_other.id, returned_ids,
            'Supervisor should NOT see logs from another supervisor interns.'
        )

    def test_supervisor_cannot_see_draft_logs(self):
        """
        Supervisors should only see SUBMITTED logs — not DRAFT logs.
        A student's unfinished draft is private until submitted.
        """
        # Create a DRAFT log for student1
        draft_log = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=3,
            activities='Draft activities not ready yet.',
            learning_points='Draft learning not ready.',
            status='DRAFT',
        )

        self.client.force_authenticate(user=self.supervisor)
        response = self.client.get('/api/logs/', format='json')

        returned_ids = [log['id'] for log in response.data]

        # The draft should NOT appear in the supervisor's view
        self.assertNotIn(
            draft_log.id, returned_ids,
            'Supervisor should not see DRAFT logs.'
        )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: Status transitions work correctly
# ══════════════════════════════════════════════════════════════════════════════

class TestLogStatusTransitions(LogbookTestCase):

    def setUp(self):
        super().setUp()

        # Create a DRAFT log to start from
        self.log = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=1,
            activities='Initial draft activities.',
            learning_points='Initial draft learning.',
            status='DRAFT',
        )

    def test_student_can_submit_draft_log(self):
        """
        A student should be able to change their DRAFT log to SUBMITTED.
        This simulates clicking the Submit button on LogFormPage.
        """
        self.client.force_authenticate(user=self.student)

        response = self.client.post(
            f'/api/logs/{self.log.id}/submit/',
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f'Submit action should return 200. Got: {response.status_code}'
        )

        # Refresh from database and check the status changed
        self.log.refresh_from_db()
        self.assertEqual(
            self.log.status, 'SUBMITTED',
            'Log status should be SUBMITTED after student submits.'
        )

    def test_student_cannot_submit_already_submitted_log(self):
        """
        Once a log is SUBMITTED, the student cannot submit it again.
        Only valid transition is DRAFT → SUBMITTED.
        """
        # Move log to SUBMITTED first
        self.log.status = 'SUBMITTED'
        self.log.save()

        self.client.force_authenticate(user=self.student)

        response = self.client.post(
            f'/api/logs/{self.log.id}/submit/',
            format='json'
        )

        # Should return 400 — can't submit an already submitted log
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'Submitting an already submitted log should return 400.'
        )

    def test_supervisor_can_review_submitted_log(self):
        """
        A workplace supervisor should be able to mark a SUBMITTED log as REVIEWED.
        This is the SUBMITTED → REVIEWED transition.
        """
        # Move log to SUBMITTED
        self.log.status = 'SUBMITTED'
        self.log.save()

        self.client.force_authenticate(user=self.supervisor)

        response = self.client.post(
            f'/api/logs/{self.log.id}/review/',
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f'Review action should return 200. Got: {response.status_code}'
        )

        self.log.refresh_from_db()
        self.assertEqual(
            self.log.status, 'REVIEWED',
            'Log status should be REVIEWED after supervisor reviews.'
        )

    def test_student_cannot_review_log(self):
        """
        A student should NOT be able to review a log.
        Only workplace supervisors can do that.
        """
        self.log.status = 'SUBMITTED'
        self.log.save()

        # Log in as student — not supervisor
        self.client.force_authenticate(user=self.student)

        response = self.client.post(
            f'/api/logs/{self.log.id}/review/',
            format='json'
        )

        # 403 = Forbidden — student doesn't have permission to review
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            'Students should not be able to review logs.'
        )

        # Status should not have changed
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'SUBMITTED')
