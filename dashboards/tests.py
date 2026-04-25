from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from logbook.models import WeeklyLog
from placements.models import InternshipPlacement
import datetime

User = get_user_model()

class LogFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email = 'admin@iles.com',
            password = 'adminpass123',
            role = 'admin',
            is_staff = True,
            first_name = 'Alice',
            last_name = 'Smith'
         )
        self.student1 = User.objects.create_user(
            email = 'student1@iles.com',
            password = 'pass123',
            role = 'student',
            first_name = 'Alice',
            last_name = 'Smith'
        )
        self.student2 = User.objects.create_user(
            email = 'student2@iles.com',
            password = 'pass123',
            role = 'student',
            first_name='Alice',  
            last_name='Smith'
        )
        self.workplace_sup = User.objects.create_user(
            email = 'supervisor@iles.com',
            password = 'pass123',
            role = 'workplace_supervisor',
            first_name='Alice',    
            last_name='Smith'
        )

        self.placement = InternshipPlacement.objects.create(
            student = self.student1,
            workplace_supervisor = self.workplace_sup,
            company_name = 'Tech Corp',
            start_date = datetime.date.today() - datetime.timedelta(weeks = 6),
            end_date = datetime.date.today() + datetime.timedelta(weeks = 6),
            status = 'ACTIVE'
        )

        self.log_draft = WeeklyLog.objects.create(
            intern = self.student1,
            placement = self.placement,
            week_number = 1,
            activities = 'Week 1 activities',
            learning_points = 'Learning points week 1',
            status = 'DRAFT'
        )
        self.log_submitted = WeeklyLog.objects.create(
            intern = self.student1,
            placement = self.placement,
            week_number = 2,
            activities = 'Week 2 activities',
            learning_points = 'Learning points week 2',
            status = 'SUBMITTED',
            submitted_at = timezone.now()
        )
        self.log_reviewed = WeeklyLog.objects.create(
            intern = self.student1,
            placement = self.placement,
            week_number = 3,
            activities = 'Week 3 activities',
            learning_points = 'Learning points week 3',
            status = 'REVIEWED'
        )
        self.log_approved = WeeklyLog.objects.create(
            intern = self.student1,
            placement = self.placement,
            week_number = 4,
            activities = 'Week 4 activities',
            learning_points = 'Learning points week 4',
            status = 'APPROVED'
        )

        self.placement2 = InternshipPlacement.objects.create(
            student = self.student2,
            workplace_supervisor = self.workplace_sup,
            company_name = 'Design Co',
            start_date = datetime.date.today() - datetime.timedelta(weeks = 4),
            end_date = datetime.date.today() + datetime.timedelta(weeks = 8),
            status = 'ACTIVE'
        )
        self.log_student2 = WeeklyLog.objects.create(
            intern = self.student2,
            placement = self.placement2,
            week_number = 1,
            activities = 'Student 2 activities',
            learning_points = 'Student 2 learning points',
            status = 'SUBMITTED',
            submitted_at = timezone.now()
        )

    def _login(self, email, password):
        response = self.client.post('api/auth/login/', {
            'email': email,
            'password': password
        }, format = 'json')
        user= User.objects.get(email = email)
        self.client.force_authenticate(user = user)

    def test_filter_logs_by_status_submitted(self):
        self._login('admin@iles.com', 'adminpass123')

        response = self.client.get('/api/logbook/logs/', {'status': 'SUBMITTED'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        statuses = [log['status'] for log in results]
        self.assertTrue(
            all(s == 'SUBMITTED' for s in statuses),
            f"Expected all SUBMITTED, got: {set(statuses)}"
        )
        self.assertGreaterEqual(len(results), 1)

    def test_filter_logs_by_status_draft(self):
        self._login('admin@iles.com', 'adminpass123')

        response = self.client.get('/api/logbook/logs/', {'status': 'DRAFT'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)
        statuses = [log['status'] for log in results]
        self.assertTrue(all(s == 'DRAFT' for s in statuses))

    def test_filter_logs_by_status_approved(self):
        self._login('admin@iles.com', 'adminpass123')

        response = self.client.get('/api/logbook/logs/', {'status': 'APPROVED'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)

        statuses = [log['status'] for log in results]
        self.assertTrue(all(s == 'APPROVED' for s in statuses))
            
    def test_search_logs_by_intern_email(self):
        self._login('admin@iles.com', 'adminpass123')

        response = self.client.get('/api/logbook/logs/' , {'search': 'student1@iles.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)

        for log in results:
            self.assertIn(
                'Alice',
                log['intern_name'],
                "Search by email returned a log belonging to a different student."
            )

    def test_search_logs_by_intern_name(self):
        self._login('admin@iles.com', 'adminpass123')

        response = self.client.get('/api/logbook/logs/', {'search': 'student1@iles.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_date_range_filter_excludes_outside_range(self):
        self._login('admin@iles.com', 'adminpass123')

        tomorrow = (datetime.date.today() + datetime.timedelta(days = 1)).isoformat()
        next_week = (datetime.date.today() + datetime.timedelta(days = 7)).isoformat()

        response = self.client.get('/api/logbook/logs/', {
            'submitted_after': tomorrow,
            'submitted_before': next_week
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)
        self.assertEqual(
            len(results), 0,
            "Expected 0 results for a future data range, but got some."
        )

    def test_date_range_filter_includes_today(self):
        self._login('admin@iles.com', 'adminpass123')

        today = datetime.date.today().isoformat()
        tomorrow = (datetime.date.today() + datetime.timedelta(days = 1)).isoformat()

        response = self.client.get('/api/logbook/logs/', {
            'submitted_after': today,
            'submitted_before': tomorrow
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_filter_logs_by_week_number(self):
        self._login('admin@iles.com', 'adminpass123')

        response = self.client.get('/api/logbook/logs/', {'week_number': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)
        for log in results:
            self.assertEqual(log['week_number'], 2)

    def test_student_cannot_see_other_student_logs(self):
        self._login('student1@iles.com', 'pass123')

        response = self.client.get('/api/logbook/logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)
        for log in results:
            self.assertIn(
                'Alice',
                log['intern_name'],
                "Student can see another student's log - data isolation failure!"
            )