# logbook/tests.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from placements.models import InternshipPlacement
from logbook.models import WeeklyLog
from reviews.models import ReviewAction

User = get_user_model()

class ReviewWorkflowIntegrationTest(TestCase):
    """
    Test the full review workflow:
    Student submits a log → Workplace supervisor reviews it → status becomes REVIEWED → audit trail created.
    """

    def setUp(self):
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            full_name='Test Student',
            role='student'
        )

        self.supervisor = User.objects.create_user(
            email='supervisor@test.com',
            password='testpass123',
            full_name='Workplace Supervisor',
            role='workplace_supervisor'
        )

        self.placement = InternshipPlacement.objects.create(
            student=self.student,
            workplace_supervisor=self.supervisor,
            company_name='Test Company',
            start_date='2025-01-01',
            end_date='2025-03-31',
            status='ACTIVE'
        )

        self.log = WeeklyLog.objects.create(
            intern=self.student,
            placement=self.placement,
            week_number=1,
            activities='Test activities',
            learning_points='Test learning points',
            status='DRAFT'
        )

        self.client = APIClient()

    def test_full_review_workflow(self):
        # ----- 1. Student submits the log -----
        login_resp = self.client.post('/api/auth/login/', {
            'email': 'student@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + login_resp.data['access'])

        # Replace 'log-submit' with the actual URL name of your submit action
        submit_url = reverse('log-submit', args=[self.log.id])
        submit_resp = self.client.post(submit_url)
        self.assertEqual(submit_resp.status_code, status.HTTP_200_OK)

        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'SUBMITTED')

        # ----- 2. Workplace supervisor reviews the log -----
        login_resp = self.client.post('/api/auth/login/', {
            'email': 'supervisor@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + login_resp.data['access'])

        # Replace 'log-review' with the actual URL name of your review action
        review_url = reverse('log-review', args=[self.log.id])
        review_resp = self.client.post(review_url)
        self.assertEqual(review_resp.status_code, status.HTTP_200_OK)

        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'REVIEWED')

        # ----- 3. Check audit trail -----
        actions = ReviewAction.objects.filter(log=self.log)
        self.assertGreaterEqual(actions.count(), 1)
        last_action = actions.last()
        self.assertEqual(last_action.action, 'REVIEWED')  # or 'APPROVED' depending on your action choice
        self.assertEqual(last_action.action_by, self.supervisor)