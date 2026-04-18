from django.test import TestCase
from django.utils import timezone 
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from logbook.models import WeeklyLog
from placements.models import InternshipPlacement

User = get_user_model()
class LogbookTestCase(TestCase):
    """Base test case with shared setup for all logbook tests."""

    def setUp(self):
        
        self.client = APIClient()
        self.student = User.objects.create_user(
            email='student1@test.com',
            password='testpass123',
            role='student',
        )
        self.student2 = User.objects.create_user(
            email='student2@test.com',
            password='testpass123',
            role='student',
        )

        self.supervisor = User.objects.create_user(
            email='supervisor1@test.com',
            password='testpass123',
            role='workplace_supervisor',
        )

        self.other_supervisor = User.objects.create_user(
            email='supervisor2@test.com',
            password='testpass123',
            role='workplace_supervisor',
        )

        self.placement = InternshipPlacement.objects.create(
            student=self.student,
            workplace_supervisor=self.supervisor,
            company_name='Test Company Ltd',
            start_date='2025-01-01',
            end_date='2025-06-30',
            status='ACTIVE',
        )

        self.placement2 = InternshipPlacement.objects.create(
            student=self.student2,
            workplace_supervisor=self.supervisor,
            company_name='Another Company',
            start_date='2025-01-01',
            end_date='2025-06-30',
            status='ACTIVE',
        )

class TestStudentCreateDraftLog(LogbookTestCase):

    def test_student_can_create_draft_log(self):
        self.client.force_authenticate(user=self.student)

        data = {
            'week_number':     1,
            'activities':      'I worked on the authentication module this week.',
            'learning_points': 'I learned how JWT tokens are structured and validated.',
            'placement':       self.placement.id,
            'status':          'DRAFT',
        }

        response = self.client.post('/api/logbook/logs/', data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            f'Expected 201 but got {response.status_code}. Response: {response.data}'
        )
        self.assertEqual(WeeklyLog.objects.count(), 1)

        log = WeeklyLog.objects.first()
        self.assertEqual(log.status, 'DRAFT')

        self.assertEqual(log.intern, self.student)

    def test_unauthenticated_user_cannot_create_log(self):
        data = {
            'week_number':     1,
            'activities':      'Some activities.',
            'learning_points': 'Some learning.',
            'placement':       self.placement.id,
        }

        response = self.client.post('/api/logbook/logs/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
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

        first_response = self.client.post('/api/logbook/logs/', data, format='json')
        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
            'First log creation should succeed.'
        )

        duplicate_data = {
            'week_number':     2, 
            'activities':      'Trying to submit again for week 2.',
            'learning_points': 'Duplicate learning points.',
            'placement':       self.placement.id,
            'status':          'DRAFT',
        }

        second_response = self.client.post('/api/logbook/logs/', duplicate_data, format='json')
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'Duplicate log for same week should return 400.'
        )

        self.assertEqual(WeeklyLog.objects.count(), 1)

    def test_student_can_create_logs_for_different_weeks(self):
        self.client.force_authenticate(user=self.student)

        self.client.post('/api/logbook/logs/', {
            'week_number': 1, 'activities': 'Week 1 activities.',
            'learning_points': 'Week 1 learning.', 'placement': self.placement.id,
        }, format='json')

        response = self.client.post('/api/logbook/logs/', {
            'week_number': 2, 'activities': 'Week 2 activities.',
            'learning_points': 'Week 2 learning.', 'placement': self.placement.id,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WeeklyLog.objects.count(), 2)

class TestSupervisorLogAccess(LogbookTestCase):

    def setUp(self):
        super().setUp() 
        self.log_student1 = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=1,
            activities='Student 1 week 1 activities.',
            learning_points='Student 1 week 1 learning.',
            status='SUBMITTED',
        )
        self.log_student2 = WeeklyLog.objects.create(
            intern=self.student2,
            placement=self.placement2,
            week_number=1,
            activities='Student 2 week 1 activities.',
            learning_points='Student 2 week 1 learning.',
            status='SUBMITTED',
        )
        self.other_student = User.objects.create_user(
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
        
        self.log_other = WeeklyLog.objects.create(
            intern=self.other_student,
            placement=self.other_placement,
            week_number=1,
            activities='Other student activities.',
            learning_points='Other student learning.',
            status='SUBMITTED',
        )

    def test_supervisor_sees_only_their_interns_logs(self):
        self.client.force_authenticate(user=self.supervisor)

        response = self.client.get('/api/logbook/logs/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data.get('results', response.data)
        returned_ids = [log['id'] for log in data]

        self.assertIn(
            self.log_student1.id, returned_ids,
            'Supervisor should see their intern student1 log.'
        )
        self.assertIn(
            self.log_student2.id, returned_ids,
            'Supervisor should see their intern student2 log.'
        )
        self.assertNotIn(
            self.log_other.id, returned_ids,
            'Supervisor should NOT see logs from another supervisor interns.'
        )

    def test_supervisor_cannot_see_draft_logs(self):
        draft_log = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=3,
            activities='Draft activities not ready yet.',
            learning_points='Draft learning not ready.',
            status='DRAFT',
        )

        self.client.force_authenticate(user=self.supervisor)
        response = self.client.get('/api/logbook/logs/', format='json')

        data = response.data.get('results', response.data)
        returned_ids = [log['id'] for log in data]
        self.assertNotIn(
            draft_log.id, returned_ids,
            'Supervisor should not see DRAFT logs.'
        )
class TestLogStatusTransitions(LogbookTestCase):

    def setUp(self):
        super().setUp()
        self.log = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=1,
            activities='Initial draft activities.',
            learning_points='Initial draft learning.',
            status='DRAFT',
        )

    def test_student_can_submit_draft_log(self):
        self.client.force_authenticate(user=self.student)

        response = self.client.post(
            f'/api/logbook/logs/{self.log.id}/submit/',
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f'Submit action should return 200. Got: {response.status_code}'
        )
        self.log.refresh_from_db()
        self.assertEqual(
            self.log.status, 'SUBMITTED',
            'Log status should be SUBMITTED after student submits.'
        )

    def test_student_cannot_submit_already_submitted_log(self):
        self.log.status = 'SUBMITTED'
        self.log.save()

        self.client.force_authenticate(user=self.student)

        response = self.client.post(
            f'/api/logbook/logs/{self.log.id}/submit/',
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'Submitting an already submitted log should return 400.'
        )

    def test_supervisor_can_review_submitted_log(self):
        self.log.status = 'SUBMITTED'
        self.log.save()

        self.client.force_authenticate(user=self.supervisor)

        response = self.client.post(
            f'/api/logbook/logs/{self.log.id}/review/',
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
        self.log.status = 'SUBMITTED'
        self.log.save()

        self.client.force_authenticate(user=self.student)

        response = self.client.post(
            f'/api/logbook/logs/{self.log.id}/review/',
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            'Students should not be able to review logs.'
        )
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'SUBMITTED')
class TestUpdatedDraftLog(LogbookTestCase):
    def setUp(self):
        super().setUp()
        self.log = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=1,
            activities='Original activities.',
            learning_points='Original learning.',
            status='DRAFT',
        )

        def test_student_can_update_own_draft_log(self):
            self.client.force_authenticate(user=self.student)

            response = self.client.path(
                f'/api/logbook/logs/{self.log.id}/',
                {'activities': 'Updated activities.'},
                format='json',
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.log.refresh_from_db()
            self.assertEqual(self.log.activities, 'Updated activities. ')

class TestCannotUpdateSubmittedLog(LogbookTestCase):

    def setUp(self):
        super().setUp()
        self.log = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=1,
            activities='Submitted activities.',
            learning_points='Submitted activities.',
            status='SUBMITTED',
        )

        def test_student_cannot_update_submitted_log(self):
            self.client.force_authenticate(user=self.student)

            response =self.client.patch(
                f'/api/logbook/logs/{self.log.id}',
                {'activities': 'Sneaky edit.'},
                format='json',
            )
            self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
            self.log.refresh_from_db()
            self.assertEqual(self.log.activities, 'Submitted activities.')

class TestOverdueDetection(LogbookTestCase):
    def test_unsubmitted_log_past_deadline_is_overdue(self):
        log = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=1,
            activities='Draft.',
            learning_points='Draft.',
            status='DRAFT',
            submitted_at=None,
        )
        self.assertTrue(log.is_overdue)

    def test_unsubmitted_log_before_deadline_is_not_overdue(self):
        log = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.student,
            week_number=200,
            activities='Future',
            learning_points='On time.',
            status='SUBMITTED',
            submitted_at=timezone.datetime(2025, 1, 15, tzinfo=timezone.utc),
        )
        self.assertTrue(log.is_overdue)

class TestSendBackFlow(LogbookTestCase):

    def setUp(self):
        super().setUp()
        self.log = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=1,
            learning_points='Ready.',
            status='SUBMITTED',
        )

    def test_supervisor_can_send_back_with_comment(self):
        self.client.force_authenticate(user=self.supervisor)

        response = self.client.post(
            f'/api/logbook/logs/{self.log.id}/send_back/',
            {'review_comment': 'Please add more detail.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'DRAFT')

        def test_send_back_requires_comment(self):
            self.client.force_authenticate(user=self.supervisor)

            response = self.client.post(
                f'/api/logbook/logs/{self.log.id}/send_back/',
                {},
                format='json',
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.log.refresh_from_db()
            self.assertEqual(self.log.status, 'SUBMITTED')

        def test_student_cannot_send_back(self):
            self.client.force_authenticate(user=self.student)

            response = self.client.post(
                f'/api/logbook/logs/{self.log.id}/send_back/',
                {'review_comment': 'Should not work.'},
                format='json',
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

            def test_full_send_back_cycle(self):
                self.client.force_authenticate(user=self.supervisor)
                self.client.post(
                    f'/api/logbook/logs/{self.log.id}/send_back/',
                    {'review_comment': 'Add more details.'},
                    format='json',
                )
                self.client.force_authenticate(user=self.student)
                edit = self.slient.patch(
                    f'/api/logbook/logs/{self.log.id}/',
                    {'activities': 'Revised with more detail.'},
                    format='json',
                )
                self.assertEqual(edit.status_code, status.HTTP_200_OK)
                resubmit = self.client.post(
                    f'/api/logbook/logs/{self.log.id}/submit/',
                    format='json',
                )
                self.assertEqual(resubmit.status_code, status.HTTP_200_OK)
                self.log.refresh_from_db()
                self.assertEqual(self.log.status, 'SUBMITTED')
