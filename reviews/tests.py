from django.db.models import Avg, Sum 
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
        user = User.objects.get(email = email)
        self.client.force_authenticate(user = user)

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
        self.student.academic_supervisor = self.academic_sup
        self.student.save()
        
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
        response = self.client.post(f'/api/logbook/logs/{log.id}/submit/')
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
        response = self.client.post(f'/api/logbook/logs/{log.id}/review/')
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
        response = self.client.post(f'/api/logbook/logs/{log.id}/send_back/', {
            'review_comment': 'Please add more detail.'
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
        
class WeightedScoreCalculationTest(TestCase):
    # weighted = (score / max_score) * weight * 100
    # total = sum of all weighted scores

    def setUp(self):
        self.client = APIClient()

        self.student = User.objects.create_user(
            email='calc_student@test.com', password='test123',
            first_name='calc', last_name='Student', role='student'
        )
        self.workplace_sup = User.objects.create_user(
            email='calc_work@test.com', password='test123',
            first_name='calc', last_name='workSup', role='workplace_supervisor'
        )
        self.academic_sup = User.objects.create_user(
            email='calc_acad@test.com', password='test123',
            first_name='calc', last_name='AcadSup', role='academic_supervisor'
        )
        self.placement = InternshipPlacement.objects.create(
            student=self.student,
            workplace_supervisor=self.workplace_sup,
            company_name='Calc Corp',
            start_date='2026-01-01',
            end_date='2026-06-30',
            status='ACTIVE'
        )

        self.c1 = EvaluationCriteria.objects.create(
            name='Technical', weight=0.60, max_score=10
        )
        self.c2 =EvaluationCriteria.objects.create(
            name='Communication', weight=0.40, max_score=10
        )

    def _login_academic(self):
        self.client.force_authenticate(user=self.academic_sup)

    def _make_reviewed_log(self, week=1):
        return WeeklyLog.objects.create(
            intern=self.student, placement=self.placement,
            week_number=week, activities='...', learning_points='...', status='REVIEWED'
        )
    def _post_evaluation(self, log, scores):
        return self.client.post('/api/evaluations/', {
            'log': log.id,
            'comments': 'Test.',
            'criteria_scores': scores 
        } , format='json')
    
    def test_perfect_scores_give_100(self):
        self._login_academic()
        log = self._make_reviewed_log(week=1)
        response = self._post_evaluation(log, {
            str(self.c1.id): 10,
            str(self.c2.id): 10,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        evaluation = Evaluation.objects.get(log=log)
        self.assertAlmostEqual(
            float(evaluation.total_score), 100.0, places=2,
            msg="Perfect scores on all criteria should return total 100.00"
        )

    def test_partial_scores_weighted_correctly(self):
        self._login_academic()
        log = self._make_reviewed_log(week=3)
        response = self._post_evaluation(log, {
            str(self.c1.id): 6,
            str(self.c2.id): 8,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        evaluation = Evaluation.objects.get(log=log)
        self.assertAlmostEqual(
            float(evaluation.total_score), 68.0, places=2,
            msg="Partial scores should be weighted correctly : (6/10)*60 + (8/10)*40 = 68"
        )

    def test_heavy_criterion_full_light_criterion_zero(self):
        self._login_academic()
        log = self._make_reviewed_log(week=4)
        response =self._post_evaluation(log, {
            str(self.c1.id): 10,
            str(self.c2.id): 0,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        evaluation = Evaluation.objects.get(log=log)
        self.assertAlmostEqual(
            float(evaluation.total_score), 60.0, places=2,
            msg="Only the heavier criterion scored - total should be 60.00" 
        )
    def test_score_above_max_is_rejected(self):
        """ Submitting a score higher than max_score must be rejected . """
        self._login_academic()
        log = self._make_reviewed_log(week=5)
        response = self._post_evaluation(log, {
            str(self.c1.id): 99, 
            str(self.c2.id): 5,
        })
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST,
            msg="Score above max_score should be rejected with 400"
        )
    
    def test_negative_score_is_rejected(self):
        """Negative scores must be rejected."""
        self._login_academic()
        log = self._make_reviewed_log(week=6)
        response = self._post_evaluation(log, {
            str(self.c1.id): -5,
            str(self.c2.id): 5,
        })
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST,
            msg="Negative score should be rejected with 400"
        )

    def test_non_existent_criterion_is_rejected(self):
        self._login_academic()
        log = self._make_reviewed_log(week=7)
        response = self._post_evaluation(log, {'9999': 5})
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST,
            msg="Non-existend criterion ID should be rejected with 400 "
        )

class RolePermissionScoringTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.student =User.objects.create_user(
            email='perm_student@test.com', password='test123',
            first_name='Perm', last_name='Student', role='student'
        )
        self.workplace_sup = User.objects.create_user(
            email='perm_work@test.com', password='test123',
            first_name='Perm', last_name='WorkSup', role='workplace_supervisor'
        )
        self.academic_sup = User.objects.create_user(
            email='perm_acad@test.com', password='test123',
            first_name='Perm', last_name='AcadSup', role='academic_supervisor'
        )
        self.placement = InternshipPlacement.objects.create(
            student=self.student,
            workplace_supervisor=self.workplace_sup,
            company_name='Perm Corp',
            start_date='2026-01-01',
            end_date='2026-06-30',
            status='ACTIVE'
        )
        self.criteria = EvaluationCriteria.objects.create(
            name='General', weight=1.00, max_score=100
        )
    def _post_evaluation(self,log, user):
        self.client.force_authenticate(user=user)
        return self.client.post('/api/evaluations/', {
            'log': log.id,
            'comments': 'Role check.',
            'criteria_scores': {str(self.criteria.id):70}
        }, format='json')
        
    def _make_log(Self, status_val, week=1):
        return WeeklyLog.objects.create(
            intern=self.student, placement=self.placement,
            week_number=week, activities='...', learning_points='...',
            status=status_val
        )
    def test_student_cannot_create_evaluation(self):
        log = self._make_log('REVIEWED', week=1)
        response = self._post_evaluation(log, self.student)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN,
            msg="Students must not be able to create evaluations"
        )
    def test_workplace_supervisor_cannot_create_evaluation(self):
        log = self._make_log('REVIEWED', week=2)
        response = self._post_evaluation(log, self.workplace_sup)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN,
            msg="Workplace supervsors must not be able ro create evaluations "
        )
    def test_draft_log_cannot_be_sorted(self):
        log = self._make_log('DRAFT', week=3)
        self.client.force_authenticate(user=self.academic_sup)
        response = self._post_evaluation(log, self.academic_sup)
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN],
            msg="Draft log must not be scoreable - must be reviewed first"
        )
    def test_approved_log_cannot_be_sorted_again(self):
        log = self._make_log('APPROVED', week=4)
        response = self._post_evaluation(log, self.academic_sup)
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN],
                msg="Already APPROVED log must not be scoreable again"
        )

    def test_log_status_becomes_approved_after_scoring(self):
        log = self._make_log('REVIEWED', week=5)
        self.client.force_authenticate(user=self.academic_sup)
        response = self._post_evaluation(log, self.academic_sup)                
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        log.refresh_from_db()
        self.assertEqual(
            log.status, 'APPROVED',
            msg="Log status should be APPROVED after being scored"
        )
 
    def test_unauthenticated_request_is_rejected(self):
        log = self._make_log('REVIEWED', week=6)
        self.client.logout()
        response = self.client.post('/api/evaluations/', {
            'log': log.id,
            'comments': 'No auth.',
            'criteria_scores': {str(self.criteria.id): 50}
        }, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            msg="Unauthenticated requests must be rejected with 401"
        )
class ScoreAggregationPerStudentTest(TestCase):
    def setUp(self):
        self.client = APIClient()
 
        self.academic_sup = User.objects.create_user(
            email='agg_acad@test.com', password='test123',
            first_name='Agg', last_name='AcadSup', role='academic_supervisor'
        )
        self.workplace_sup = User.objects.create_user(
            email='agg_work@test.com', password='test123',
            first_name='Agg', last_name='WorkSup', role='workplace_supervisor'
        )
        self.student_a = User.objects.create_user(
            email='agg_studentA@test.com', password='test123',
            first_name='Student', last_name='A', role='student'
        )
        self.student_b = User.objects.create_user(
            email='agg_studentB@test.com', password='test123',
            first_name='Student', last_name='B', role='student'
        )
        self.placement_a = InternshipPlacement.objects.create(
            student=self.student_a,
            workplace_supervisor=self.workplace_sup,
            company_name='Corp A',
            start_date='2026-01-01',
            end_date='2026-06-30',
            status='ACTIVE'
        )
        self.placement_b = InternshipPlacement.objects.create(
            student=self.student_b,
            workplace_supervisor=self.workplace_sup,
            company_name='Corp B',
            start_date='2026-01-01',
            end_date='2026-06-30',
            status='ACTIVE'
        )
        self.criteria = {
            'technical': EvaluationCriteria.objects.create(
                name='Technical', weight=0.60, max_score=10),
            'communication': EvaluationCriteria.objects.create(
                name='Communication', weight=0.40, max_score=10),
        }
 
    def _make_reviewed_log(self, student, placement, week):
        return WeeklyLog.objects.create(
            intern=student, placement=placement,
            week_number=week, activities='...', learning_points='...',
            status='REVIEWED'
        )
 
    def _post_evaluation(self, log, scores):
        self.client.force_authenticate(user=self.academic_sup)
        return self.client.post('/api/evaluations/', {
            'log': log.id,
            'comments': 'Aggregation test.',
            'criteria_scores': scores
        }, format='json')
 
    def _scores(self, value):
        return {str(c.id): value for c in self.criteria.values()}
 
    def test_multiple_logs_for_one_student_all_stored(self):
        """All evaluations for a student are retrievable ."""
        log1 = self._make_reviewed_log(self.student_a, self.placement_a, week=1)
        log2 = self._make_reviewed_log(self.student_a, self.placement_a, week=2)
        self._post_evaluation(log1, self._scores(8))
        self._post_evaluation(log2, self._scores(6))
 
        count = Evaluation.objects.filter(log__intern=self.student_a).count()
        self.assertEqual(count, 2,
            msg="Both evaluations for student A should be stored")
 
    def test_average_score_across_logs(self):
        log1 = self._make_reviewed_log(self.student_a, self.placement_a, week=3)
        log2 = self._make_reviewed_log(self.student_a, self.placement_a, week=4)
        self._post_evaluation(log1, self._scores(8))
        self._post_evaluation(log2, self._scores(6))
 
        avg = (
            Evaluation.objects
            .filter(log__intern=self.student_a)
            .aggregate(avg=Avg('total_score'))['avg']
        )
        self.assertAlmostEqual(float(avg), 70.0, places=1,
            msg="Average of 80 and 60 should be 70.00")
 
    def test_total_score_sum_per_student(self):
        log1 = self._make_reviewed_log(self.student_a, self.placement_a, week=5)
        log2 = self._make_reviewed_log(self.student_a, self.placement_a, week=6)
        self._post_evaluation(log1, self._scores(8))
        self._post_evaluation(log2, self._scores(6))
 
        total = (
            Evaluation.objects
            .filter(log__intern=self.student_a)
            .aggregate(total=Sum('total_score'))['total']
        )
        self.assertAlmostEqual(float(total), 140.0, places=1,
            msg="Sum of 80 and 60 should be 140.00")
 
    def test_scores_isolated_between_students(self):
        """Student B's evaluations must not appear in Student A's queryset."""
        log_a = self._make_reviewed_log(self.student_a, self.placement_a, week=7)
        log_b = self._make_reviewed_log(self.student_b, self.placement_b, week=1)
        self._post_evaluation(log_a, self._scores(9))
        self._post_evaluation(log_b, self._scores(5))
 
        evals_a = Evaluation.objects.filter(log__intern=self.student_a)
        evals_b = Evaluation.objects.filter(log__intern=self.student_b)
 
        self.assertEqual(evals_a.count(), 1,
            msg="Student A should have exactly 1 evaluation")
        self.assertEqual(evals_b.count(), 1,
            msg="Student B should have exactly 1 evaluation")
        self.assertNotEqual(
            evals_a.first().id, evals_b.first().id,
            msg="Student A and B evaluations must not be the same record"
        )
 
    def test_student_with_no_evaluations_returns_empty(self):
        """A student who has never been scored returns an empty queryset."""
        count = Evaluation.objects.filter(log__intern=self.student_a).count()
        self.assertEqual(count, 0,
            msg="Student with no evaluations should return empty queryset")
 
    def test_api_student_only_sees_own_evaluations(self):
        """Via the API a student must only receive their own evaluations."""
        log_a = self._make_reviewed_log(self.student_a, self.placement_a, week=8)
        log_b = self._make_reviewed_log(self.student_b, self.placement_b, week=2)
        self._post_evaluation(log_a, self._scores(10))
        self._post_evaluation(log_b, self._scores(5))
 
        self.client.force_authenticate(user=self.student_a)
        response = self.client.get('/api/evaluations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
 
        returned_log_ids = [
            e['log'] for e in response.data.get('results', response.data)
        ]
        self.assertIn(log_a.id, returned_log_ids,
            msg="Student A should see their own evaluation")
        self.assertNotIn(log_b.id, returned_log_ids,
            msg="Student A must not see Student B's evaluation")
 
class ScoringNotificationTest(TestCase):
    """
    Verifies notifications fired specifically by the scoring action
    (REVIEWED → APPROVED transition).
    """
    def setUp(self):
        self.client = APIClient()
 
        self.student = User.objects.create_user(
            email='score_student@test.com', password='test123',
            first_name='Score', last_name='Student', role='student'
        )
        self.workplace_sup = User.objects.create_user(
            email='score_work@test.com', password='test123',
            first_name='Score', last_name='WorkSup', role='workplace_supervisor'
        )
        self.academic_sup = User.objects.create_user(
            email='score_acad@test.com', password='test123',
            first_name='Score', last_name='AcadSup', role='academic_supervisor'
        )
        self.placement = InternshipPlacement.objects.create(
            student=self.student,
            workplace_supervisor=self.workplace_sup,
            company_name='Score Corp',
            start_date='2026-01-01',
            end_date='2026-06-30',
            status='ACTIVE'
        )
        self.criteria = EvaluationCriteria.objects.create(
            name='General', weight=1.00, max_score=100
        )
 
    def _make_reviewed_log(self, week=1):
        return WeeklyLog.objects.create(
            intern=self.student, placement=self.placement,
            week_number=week, activities='...', learning_points='...',
            status='REVIEWED'
        )
 
    def _score_log(self, log):
        self.client.force_authenticate(user=self.academic_sup)
        return self.client.post('/api/evaluations/', {
            'log': log.id,
            'comments': 'Well done.',
            'criteria_scores': {str(self.criteria.id): 85}
        }, format='json')
 
    def test_notification_created_when_log_is_scored(self):
        """Scoring a log must produce a notification for the student."""
        log = self._make_reviewed_log(week=1)
        before = Notification.objects.filter(recipient=self.student).count()
        self._score_log(log)
        after = Notification.objects.filter(recipient=self.student).count()
        self.assertGreater(after, before,
            msg="Scoring a log should create at least one notification for the student")
 
    def test_notification_type_is_log_approved(self):
        """The notification fired on scoring must have type LOG_APPROVED."""
        log = self._make_reviewed_log(week=2)
        self._score_log(log)
        notif = (
            Notification.objects
            .filter(recipient=self.student, notification_type='LOG_APPROVED')
            .order_by('-created_at')
            .first()
        )
        self.assertIsNotNone(notif,
            msg="A LOG_APPROVED notification should exist for the student after scoring")
 
    def test_notification_is_unread_by_default(self):
        """Newly created scoring notification must default to is_read=False."""
        log = self._make_reviewed_log(week=3)
        self._score_log(log)
        notif = (
            Notification.objects
            .filter(recipient=self.student, notification_type='LOG_APPROVED')
            .order_by('-created_at')
            .first()
        )
        self.assertFalse(notif.is_read,
            msg="Scoring notification should be unread when first created")
 
    def test_notification_message_mentions_week_number(self):
        """Notification message should reference the correct week number."""
        log = self._make_reviewed_log(week=4)
        self._score_log(log)
        notif = (
            Notification.objects
            .filter(recipient=self.student, notification_type='LOG_APPROVED')
            .order_by('-created_at')
            .first()
        )
        self.assertIn('4', notif.message,
            msg="Notification message should mention the week number (4)")
 
    def test_no_duplicate_notifications_on_single_scoring(self):
        """A single scoring event must not create more than one LOG_APPROVED notification."""
        log = self._make_reviewed_log(week=5)
        self._score_log(log)
        count = Notification.objects.filter(
            recipient=self.student,
            notification_type='LOG_APPROVED'
        ).count()
        self.assertEqual(count, 1,
            msg="Exactly one LOG_APPROVED notification should be created per scoring event")
 
    def test_scoring_does_not_notify_wrong_student(self):
        """Another student's inbox must remain empty after this scoring."""
        other_student = User.objects.create_user(
            email='other_score@test.com', password='test123',
            first_name='Other', last_name='Student', role='student'
        )
        log = self._make_reviewed_log(week=6)
        self._score_log(log)
        count = Notification.objects.filter(recipient=other_student).count()
        self.assertEqual(count, 0,
            msg="Scoring one student's log must not create notifications for other students")
 
