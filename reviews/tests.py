from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from placements.models import InternshipPlacement
from logbook.models import WeeklyLog
from reviews.models import EvaluationCriteria, Evaluation, Notification

User = get_user_model()

class EvaluationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.student = User.objects.create_user(
            email = 'student1@test.com', password = 'student123',
            first_name = 'Test', last_name = 'Student', role = 'student'
        )
        self.other_student = User.objects.create_user(
            email = 'other@test.com', password = 'test123',
            first_name = 'Other', last_name = 'Student', role = 'student'
        )
        self.academic_sup = User.objects.create_user(
            email = 'academic@test.com', password = 'test123',
            first_name = 'Academic', last_name = 'Supervisor', role = 'academic_supervisor'
        )
        self.workplace_sup = User.objects.create_user(
            email = 'workplace@test.com', password = 'test123',
            first_name = 'Workplace', last_name = 'Supervisor', role = 'workplace_supervisor'
        )

        self.placement = InternshipPlacement.objects.create(
            student = self.student,
            workplace_supervisor = self.workplace_sup,
            company_name = 'Corp',
            start_date = '2026-01-01',
            end_date = '2026-06-30',
            status = 'ACTIVE'
        )

        self.criteria = {
            'technical': EvaluationCriteria.objects.create(
                name = 'Technical Skills', weight = 0.30, max_score = 100),
            'communication': EvaluationCriteria.objects.create(
                name = 'Communication', weight = 0.20, max_score = 100),
            'punctuality': EvaluationCriteria.objects.create(
                name = 'Punctuality', weight = 0.15, max_score = 100),
            'initiative': EvaluationCriteria.objects.create(
                name = 'Initiative', weight = 0.20, max_score = 100),
            'professionalism': EvaluationCriteria.objects.create(
                name = 'Professionalism', weight = 0.15, max_score =100),
        }
        
    def _login(self, email, password = 'test123'):
        response = self.client.post('/api/token/',
            {'email': email, 'password': password}, format = 'json')
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION = f'Bearer {token}')

    def _make_reviewed_log(self, week = 1):
        return WeeklyLog.objects.create(
            intern = self.student, placement = self.placement,
            week_number = week, activities = '...', learning_points = '....',
            status = 'REVIEWED'
        )
    
    def test_score_calculation_uses_criteria_weights(self):
        log = self._make_reviewed_log(week = 1)
        self._login('academic@test.com')

        criteria_scores = {
            str(c.id): 80
            for c in self.criteria.values()
        }

        response = self.client.post('/api/evaluations/', {
            'log': log.id,
            'comments': 'Good.',
            'criteria_scores': criteria_scores
        }, format = 'json')

        self. assertEqual(response.status_code, status.HTTP_201_CREATED)
        evaluation = Evaluation.objects.get(log = log)
        self.assertAlmostEqual(
            float(evaluation.total_score), 80.0, places = 1,
            msg = "Weighted total score should be 80.0 when all individual scores are 80."
        )

    def test_academic_supervisor_cannot_score_submitted_log(self):
        submitted_log = WeeklyLog.objects.create(
            intern = self.student, placement = self.placement,
            week_number = 2, activities = '...', learning_points = '...',
            status = 'SUBMITTED'
        )
        self._login('academic@test.com')

        criteria_scores = {str(c.id): 70 for c in self.criteria.values()}
        response = self.client.post('/api/evaluations/', {
            'log': submitted_log.id,
            'comments': 'Skipping the queue.',
            'criteria_scores': criteria_scores
        }, format = 'json')

        self.assertIn(response.status_code,
                [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN],
                "Scoring a SUBMITTED log should be rejected - it must be REVIEWED first"
            )

    def test_student_cannot_see_other_students_evaluation(self):
        other_placement = InternshipPlacement.objects.create(
            student = self.other_student,
            workplace_supervisor = self.workplace_sup,
            company_name = 'Other Corp',
            start_date = '2026-01-01',
            end_date = '2026-06-30',
            status = 'ACTIVE'
        )
        other_log = WeeklyLog.objects.create(
            intern = self.other_student, placement = other_placement,
            week_number = 1, activities = '...', learning_points = '...',
            status = 'REVIEWED'
        )
        criteria_scores = {str(c.id): 90 for c in self.criteria.values()}
        Evaluation.objects.create(
            log = other_log,
            academic_supervisor = self.academic_sup,
            total_score = 90,
            criteria_scores = criteria_scores,
            comments = 'Excellent.'
        )

        self._login('student1@test.com')
        response = self.client.get('/api/evaluations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        evaluation_ids = [e['id'] for e in response.data.get('results', response.data)]
        other_evals = Evaluation.objects.filter(log__intern = self.other_student)
        for other_eval in other_evals:
            self.assertNotIn(other_eval.id, evaluation_ids,
            "Student must not see another student's evaluation scores.")

class NotificationSignalTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            email = 'student1@test.com', password = 'student123',
            first_name = 'Test', last_name = 'Student', role = 'student'
        )
        self.workplace_sup = User.objects.create_user(
            email = 'workplace@test.com', password = 'test123', 
            first_name = 'Test', last_name = 'Supervisor', role = 'workplace_supervisor'
        )
        self.academic_sup = User.objects.create_user(
            email = 'academic@test.com', password = 'test123',
            first_name = 'Test', last_name = 'Supervisor', role = 'academic_supervisor'
        )
        self.placement = InternshipPlacement.objects.create(
            student = self.student,
            workplace_supervisor = self.workplace_sup,
            company_name = 'Test Corp',
            start_date = '2026-06-01',
            end_date = '2026-08-31',
            status = 'ACTIVE'
        )

    def _login(self, email, password):
        response = self.client.post('/api/auth/login/', {
            'email': email, 'password': password
        }, format = 'json')
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION = f'Bearer {token}')
        return token

    def test_submit_log_creates_notification_for_workplace_supervisor(self):
        self._login('student1@test.com', 'student123')
        log = WeeklyLog.objects.create(
            intern = self.student,
            placement = self.placement,
            week_number = 1,
            activities = 'Did tasks this week',
            learning_points = 'Learned a lot.',
            status = 'DRAFT'
        )
        response = self.client.post(f'/api/logs/{log.id}/submit/')
        self. assertEqual(response.status_code, status.HTTP_200_OK)

        unread = Notification.objects.filter(
            recipient = self.workplace_sup,
            is_read = False,
            notification_type = 'LOG_SUBMITTED'
        )
        self.assertEqual(unread.count(), 1,
                         "Workplace supervisor should receive a LOG_SUBMITTED notification")
        
    def test_mark_notification_as_read_decreases_unread_count(self):
        notif = Notification.objects.create(
            recipient = self.workplace_sup,
            message = 'Student submitted a log.',
            notification_type = 'LOG_SUBMITTED',
            is_read = False
        )

        self._login('workplace@test.com', 'test123')
        response = self.client.get(f'/api/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mark_response = self.client.patch(f'/api/notifications/{notif.id}/mark_as_read/')
        self.assertEqual(mark_response.status_code, status.HTTP_200_OK)

        unread_count = Notification.objects.filter(
            recipient = self.workplace_sup,
            is_read = False
        ).count()
        self.assertEqual(unread_count, 0,
            "Marking a notification as read should make unread count 0")
        
    def test_reviewed_log_notifies_academic_supervisor(self):
        log = WeeklyLog.objects.create(
            intern = self.student,
            placement = self.placement,
            week_number = 2,
            activities = 'Week 2 work.',
            learning_points = 'More learning',
            status = 'SUBMITTED'
        )
        self._login('workplace@test.com', 'test123')
        response = self.client.post(f'/api/logs/{log.id}/review/')
        self. assertEqual(response.status_code, status.HTTP_200_OK)

        notif = Notification.objects.filter(
            recipient = self.academic_sup,
            notification_type = 'LOG_REVIEWED'
        )
        self.assertEqual(notif.count(), 1,
                         "Academic supervisor should be notified when a log is reviewed")
        
    def test_sent_back_back_log_notifies_student(self):
        log = WeeklyLog.objects.create(
            intern = self.student,
            placement = self.placement,
            week_number = 3,
            activities = 'Week 3.',
            learning_points = 'Learned.',
            status = 'SUBMITTED'
        )
        self._login('workplace@test.com', 'test123')
        response = self.client.post(f'/api/logs/{log.id}/send_back/', {
            'comment': 'Please add more detail.'
            }, format = 'json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notif = Notification.objects.filter(
            recipient = self.student,
            notification_type = 'LOG_SENT_BACK'
        )
        self.assertEqual(notif.count(), 1,
                         "Student should be notified when their log is sent back")
        
    def test_approved_log_notifies_student(self):
        log = WeeklyLog.objects.create(
            intern = self.student,
            placement = self.placement,
            week_number = 4,
            activities = 'Week 4',
            learning_points = 'Learned more.',
            status = 'REVIEWED'
        )

        self._login('academic@test.com', 'test123')
        response = self.client.post('/api/evaluations/', {
            'log': log.id,
            'comments': 'Good work.',
            'criteria_scores': {}
        }, format = 'json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        notif = Notification.objects.filter(
            recipient = self.student,
            notification_type = 'LOG_APPROVED'
        )
        self.assertEqual(notif.count(), 1,
                         "Student should be notified when their  log is approved/scored.")