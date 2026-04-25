from urllib import response

from django.urls import reverse

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from logbook.models import WeeklyLog
from placements.models import InternshipPlacement
import datetime
from dashboards.factories import (
    make_student,
    make_supervisor,
    make_academic,
    make_admin,
    make_placement,
    make_log,
    make_evaluation,
    make_criteria,
    reset_week_counter,
)

LOGS_URL = "/api/logs/"
EVALUATIONS_URL = "/api/evaluations/"
ADMIN_STATS_URL = "/api/dashboards/admin-stats/"


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
            first_name='Bob',  
            last_name='Williams'
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

        response = self.client.get('/api/logs/', {'status': 'SUBMITTED'})
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

        response = self.client.get('/api/logs/', {'status': 'DRAFT'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)
        statuses = [log['status'] for log in results]
        self.assertTrue(all(s == 'DRAFT' for s in statuses))

    def test_filter_logs_by_status_approved(self):
        self._login('admin@iles.com', 'adminpass123')

        response = self.client.get('/api/logs/', {'status': 'APPROVED'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)

        statuses = [log['status'] for log in results]
        self.assertTrue(all(s == 'APPROVED' for s in statuses))
            
    def test_search_logs_by_intern_email(self):
        self._login('admin@iles.com', 'adminpass123')

        response = self.client.get('/api/logs/' , {'search': 'student1@iles.com'})
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

        response = self.client.get('/api/logs/', {'search': 'student1@iles.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_date_range_filter_excludes_outside_range(self):
        self._login('admin@iles.com', 'adminpass123')

        tomorrow = (datetime.date.today() + datetime.timedelta(days = 1)).isoformat()
        next_week = (datetime.date.today() + datetime.timedelta(days = 7)).isoformat()

        response = self.client.get('/api/logs/', {
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

        response = self.client.get('/api/logs/', {
            'submitted_after': today,
            'submitted_before': tomorrow
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_filter_logs_by_week_number(self):
        self._login('admin@iles.com', 'adminpass123')

        response = self.client.get('/api/logs/', {'week_number': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)
        for log in results:
            self.assertEqual(log['week_number'], 2)

    def test_student_cannot_see_other_student_logs(self):
        self._login('student1@iles.com', 'pass123')

        response = self.client.get('/api/logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)
        for log in results:
            self.assertIn(
                'Alice',
                log['intern_name'],
                "Student can see another student's log - data isolation failure!"
            )


class DashboardTestBase(TestCase):

    def setUp(self):
        reset_week_counter()
        self.client = APIClient()

        self.student    = make_student()
        self.student2   = make_student()   # used for isolation tests
        self.supervisor = make_supervisor()
        self.academic   = make_academic()
        self.admin      = make_admin()

        self.placement = make_placement(self.student, self.supervisor)
        self.placement2 = make_placement(self.student2, self.supervisor)

        self.criteria = make_criteria()

    def _auth(self, user):
        self.client.force_authenticate(user=user)
        
        
    def _get(self, url, params = None):
        return self.client.get(url,params or {})
    

class StudentStatsTests(DashboardTestBase):

    def test_returns_correct_submitted_count(self):
        
        make_log(self.student, self.placement, status="SUBMITTED")
        make_log(self.student, self.placement, status="SUBMITTED")
        make_log(self.student, self.placement, status="DRAFT")

        self._auth(self.student)
        response = self._get('/api/student-stats/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["logs_submitted"],2)

    def test_returns_correct_pending_reviews_count(self):

        make_log(self.student, self.placement, status="SUBMITTED")
        make_log(self.student, self.placement, status="SUBMITTED")
        make_log(self.student, self.placement, status="DRAFT")

        self._auth(self.student)
        response = self._get('/api/student-stats/')

        self.assertEqual(response.status_code, 200)
        
        print("\nStudent stats keys:", list(response.data.keys()))
        print("Student stats data:", dict(response.data))

        pending = (response.data.get("pending_reviews"))
        self.assertEqual(pending, 2)

    def test_returns_zero_counts_for_fresh_student(self):
        self._auth(self.student2)
        response = self._get('/api/student-stats/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["logs_submitted"],0)
        self.assertEqual(response.data["pending_reviews"],0)

    def test_requires_authentication(self):
        self.client.logout()
        response = self._get('/api/student-stats/')
        self.assertEqual(response.status_code, 401)

    def test_student_only_sees_own_status(self):
        make_log(self.student2, self.placement2, status="SUBMITTED")
        make_log(self.student2, self.placement2, status="SUBMITTED")
        make_log(self.student2, self.placement2, status="SUBMITTED")
        make_log(self.student, self.placement, status="SUBMITTED")

        self._auth(self.student)
        response = self._get('/api/student-stats/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["logs_submitted"],1)

class StudentProgressTests(DashboardTestBase):

    def test_returns_all_log_for_student(self):
        make_log(self.student, self.placement, status="APPROVED", week_number=1)
        make_log(self.student, self.placement, status="SUBMITTED", week_number=2)
        make_log(self.student, self.placement, status="DRAFT", week_number=3)

        self._auth(self.student)
        response = self._get('/api/student-progress/me/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_approved_log_includes_score(self):
        log = make_log(self.student, self.placement, status="APPROVED", week_number=1)
        make_evaluation(log, self.academic, self.criteria)

        self._auth(self.student)
        response = self._get('/api/student-progress/me/')

        self.assertEqual(response.status_code, 200)
        week_1= next(r for r in response.data if r["week_number"] == 1)
        self.assertIsNotNone(week_1["score_if_approved"])
        self.assertGreater(week_1["score_if_approved"], 0)

    def test_unapproved_log_has_null_score(self):
        make_log(self.student, self.placement, status="SUBMITTED", week_number=1)

        self._auth(self.student)
        response = self._get('/api/student-progress/me/')

        week_1 = next(r for r in response.data if r["week_number"] == 1)
        self.assertIsNone(week_1["score_if_approved"])

    def test_returns_ordered_by_week_number(self):
        make_log(self.student, self.placement, status="APPROVED", week_number=3)
        make_log(self.student, self.placement, status="SUBMITTED", week_number=1)
        make_log(self.student, self.placement, status="DRAFT", week_number=2)

        self._auth(self.student)
        response = self._get('/api/student-progress/me/')

        week_numbers = [r["week_number"] for r in response.data]
        self.assertEqual(week_numbers, sorted(week_numbers))

    def test_student_cannot_access_another_student_progress(self):
        make_log(self.student, self.placement, status="APPROVED", week_number=1)
        make_log(self.student, self.placement, status="APPROVED", week_number=2)
        make_log(self.student2, self.placement2, status="APPROVED", week_number=1)

        self._auth(self.student)
        response = self._get('/api/student-progress/me/')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(response.data), 1)

class WorkplaceStatsTests(DashboardTestBase):

    def test_pending_reviews_count_is_correct(self):
        make_log(self.student, self.placement, status="SUBMITTED")
        make_log(self.student, self.placement, status="SUBMITTED")
        make_log(self.student2, self.placement2, status="SUBMITTED")
        make_log(self.student2, self.placement2, status="REVIEWED")

        self._auth(self.supervisor)
        response = self._get('/api/workplace-stats/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pending_reviews"],3)

    def test_total_interns_reflects_active_placements(self):
        self._auth(self.supervisor)
        response = self._get('/api/workplace-stats/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_interns"],2)

    def test_supervisor_only_sees_own_stats(self):

        supervisor2 = make_supervisor()
        student3 = make_student()
        placement3 = make_placement(student3, supervisor2)

        make_log(student3, placement3, status="SUBMITTED")

        make_log(self.student, self.placement, status="SUBMITTED")
        make_log(self.student2, self.placement2, status="SUBMITTED")

        self._auth(self.supervisor)
        response = self._get('/api/workplace-stats/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pending_reviews"],2)
        self.assertEqual(response.data["total_interns"],2)

    def test_student_cannot_access_workplace_stats(self):
        self._auth(self.student)
        response = self._get('/api/workplace-stats/')

        self.assertEqual(response.status_code, 403)

class AcademicStatsTests(DashboardTestBase):

    def test_logs_to_score_counts_reviewed_logs(self):
        make_log(self.student, self.placement, status="REVIEWED")
        make_log(self.student, self.placement, status="REVIEWED")
        make_log(self.student2, self.placement2, status="SUBMITTED")

        self._auth(self.academic)
        response = self._get('/api/academic-stats/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["logs_to_score"],2)

    def test_avg_cohort_score_is_correct(self):
        log1 = make_log(self.student, self.placement, status="APPROVED")
        log2 = make_log(self.student2, self.placement2, status="APPROVED")

        make_evaluation(log1, self.academic, self.criteria, score=80.60)
        make_evaluation(log2, self.academic, self.criteria, score=60.0)

        self._auth(self.academic)
        response = self._get('/api/academic-stats/')

        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(float(response.data["avg_cohort_score"]),70.0, places=1)

    def test_avg_cohort_score_is_none_when_no_evaluations(self):
        self._auth(self.academic)
        response = self._get('/api/academic-stats/')

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["avg_cohort_score"])

    def test_student_cannot_access_academic_stats(self):
        self._auth(self.student)
        response = self._get('/api/academic-stats/')

        self.assertEqual(response.status_code, 403)


class CohortScoresTests(DashboardTestBase):

    def test_returns_one_entry_per_student(self):
        make_log(self.student, self.placement, status="DRAFT")
        make_log(self.student2, self.placement2, status="DRAFT")

        self._auth(self.academic)
        response = self._get('/api/cohort-scores/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_approved_log_count_is_accurate(self):
        make_log(self.student, self.placement, status="APPROVED", week_number=1)
        make_log(self.student, self.placement, status="APPROVED", week_number=2)
        make_log(self.student, self.placement, status="SUBMITTED", week_number=3)

        self._auth(self.academic)
        response = self._get('/api/cohort-scores/')

        self.assertEqual(response.status_code, 200)
        print("\nCohort scores response:", response.data)

        student_full_name = self.student.get_full_name.strip()
        student_row = None
        for row in response.data:
            name_in_row = (
                row.get("student_name") or
                row.get("full_name") or
                row.get("name") or
                (row.get("student", {}).get("full_name","") 
                if isinstance(row.get("student"), dict) else "")
            )
            if name_in_row.strip() == student_full_name or str(row.get("student_id")) == str(self.student.id):
                student_row = row
                break

        self.assertIsNotNone(student_row, f"Student not found in response. Response was:{response.data}")
        self.assertEqual(student_row["approved_logs"], 2)
        self.assertEqual(student_row["total_logs"], 3)


    def test_results_are_sorted_by_avg_score_descending(self):
        log1 = make_log(self.student, self.placement, status="APPROVED", week_number=1)
        log2 = make_log(self.student2, self.placement2, status="APPROVED", week_number=1)

        make_evaluation(log1, self.academic, self.criteria, score=90.0)
        make_evaluation(log2, self.academic, self.criteria, score=50.0)

        self._auth(self.academic)
        response = self._get('/api/cohort-scores/')

        scores = [r["avg_score"] for r in response.data if r["avg_score"] is not None]
        self.assertEqual(scores, sorted(scores, reverse=True))


class AdminStatsTests(DashboardTestBase):

    def test_total_students_count_is_correct(self):
        self._auth(self.admin)

        try:
            url=reverse('admin-stats')
            print(f"\nDEBUG: the URL according to Django is:{url}")
        except Exception as e:
            print(f"\nDEBUG: Django could not find 'admin-stats'. Error:{e}")
            url = ADMIN_STATS_URL

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_students"],2)

    def test_active_placements_count_is_correct(self):
        self._auth(self.admin)
        response = self._get('ADMIN_STATS_URL')

        print(f"\nDEBUG: URL used is {ADMIN_STATS_URL}")
        print(f"DEBUG: Status Code is {response.status_code}")
        print(f"DEBUG: Data returned is {response.data}")


        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["active_placements"],2)

    def test_approved_logs_count_is_correct(self):
        make_log(self.student, self.placement, status="APPROVED")
        make_log(self.student, self.placement, status="APPROVED")
        make_log(self.student2, self.placement2, status="APPROVED")
        make_log(self.student2, self.placement2, status="SUBMITTED")
        make_log(self.student2, self.placement2, status="DRAFT")

        self._auth(self.admin)
        response = self._get('ADMIN_STATS_URL')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["approved_logs"],3)
        self.assertEqual(response.data["total_logs"],5)

    def test_student_cannot_access_admin_stats(self):
        self._auth(self.student)
        response = self._get('ADMIN_STATS_URL')

        self.assertEqual(response.status_code, 403)

    def test_supervisor_cannot_access_admin_stats(self):
        self._auth(self.supervisor)
        response = self._get('ADMIN_STATS_URL')

        self.assertEqual(response.status_code, 403)

class LogsPerWeekTests(DashboardTestBase):

    def test_returns_correct_counts_per_week(self):
        make_log(self.student, self.placement, status="SUBMITTED", week_number=1)
        make_log(self.student2, self.placement2, status="SUBMITTED", week_number=1)
        make_log(self.student, self.placement, status="APPROVED", week_number=2)
        make_log(self.student2, self.placement2, status="APPROVED", week_number=2)
        make_log(self.student2, self.placement2, status="DRAFT", week_number=3)

        self._auth(self.admin)
        response = self._get('/api/logs-per-week/')

        self.assertEqual(response.status_code, 200)
        by_week ={r["week_number"]: r["count"] for r in response.data}
        
        self.assertEqual(by_week[1],2)
        self.assertEqual(by_week[2],2)
        self.assertEqual(by_week[3],1)

    def test_weeks_with_no_logs_are_excluded(self):
        make_log(self.student, self.placement, status="SUBMITTED", week_number=1)
       
        self._auth(self.admin)
        response = self._get('/api/logs-per-week/')

        week_numbers = [r["week_number"] for r in response.data]
        self.assertNotIn(4, week_numbers)
        self.assertNotIn(12, week_numbers)

    def test_student_cannot_access_this_endpoint(self):
        self._auth(self.student)
        response = self._get('/api/logs-per-week/')

        self.assertEqual(response.status_code, 403)


class StatusDistributionTests(DashboardTestBase):

    def test_all_four_statuses_are_counted_correctly(self):
        make_log(self.student, self.placement, status="DRAFT", week_number=1)
        make_log(self.student, self.placement, status="SUBMITTED", week_number=2)
        make_log(self.student2, self.placement2, status="SUBMITTED", week_number=1)
        make_log(self.student2, self.placement2, status="REVIEWED", week_number=2)
        make_log(self.student, self.placement, status="APPROVED", week_number=3)
        make_log(self.student2, self.placement2, status="APPROVED", week_number=3)
        make_log(self.student, self.placement, status="APPROVED", week_number=4)

        self._auth(self.admin)
        response = self._get('/api/status-distribution/')

        self.assertEqual(response.status_code, 200)

        by_status = {r["status"]: r["count"] for r in response.data}

        self.assertEqual(by_status.get("DRAFT"),1)
        self.assertEqual(by_status.get("SUBMITTED"),2)
        self.assertEqual(by_status.get("REVIEWED"),1)
        self.assertEqual(by_status.get("APPROVED"),3)

    def test_statuses_with_zero_logs_are_excluded(self):
        make_log(self.student, self.placement, status="DRAFT", week_number=1)

        self._auth(self.admin)
        response = self._get("/api/status-distribution/")

        statuses_returned = [r["status"] for r in response.data]
        self.assertNotIn("REVIEWED",  statuses_returned)
        self.assertNotIn("SUBMITTED", statuses_returned)
        self.assertNotIn("APPROVED",  statuses_returned)
        self.assertIn("DRAFT", statuses_returned)
    

class DashboardFilterTests(DashboardTestBase):

    def test_logs_endpoint_filters_by_status(self):
        make_log(self.student, self.placement, status="SUBMITTED")
        make_log(self.student, self.placement, status="SUBMITTED")
        make_log(self.student, self.placement, status="DRAFT")
        make_log(self.student, self.placement, status="APPROVED")

        self._auth(self.student)
        response = self._get("/api/logs/", {"status": "SUBMITTED"})

        self.assertEqual(response.status_code, 200)
        data = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(data), 2)
        self.assertTrue(all(log["status"] == "SUBMITTED" for log in data))

    def test_logs_endpoint_filters_by_week_number(self):
        make_log(self.student, self.placement, status="DRAFT", week_number=1)
        make_log(self.student, self.placement, status="DRAFT", week_number=2)
        make_log(self.student, self.placement, status="DRAFT", week_number=3)

        self._auth(self.student)
        response = self._get("/api/logs/", {"week_number": 2})

        data = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["week_number"], 2)

    def test_logs_endpoint_filters_by_status_and_supervisor(self):

        supervisor2 = make_supervisor()
        student3 = make_student()
        placement3 = make_placement(student3, supervisor2)
        make_log(self.student,  self.placement,  status="SUBMITTED")
        make_log(self.student2, self.placement2, status="SUBMITTED")

        make_log(student3, placement3, status="SUBMITTED")

        self._auth(self.supervisor)
        response = self._get("/api/logs/", {"status": "SUBMITTED", "supervisor": "me"})

        data = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(data), 2)

class DataIsolationTests(DashboardTestBase):

    def test_student_cannot_see_another_students_logs(self):
        make_log(self.student2, self.placement2, status="SUBMITTED")
        make_log(self.student2, self.placement2, status="SUBMITTED")
        make_log(self.student2, self.placement2, status="APPROVED")
        make_log(self.student,  self.placement,  status="DRAFT")
    
        self._auth(self.student)
        response = self._get("/api/logs/")

        self.assertEqual(response.status_code, 403)

        data = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(data), 1)

    def test_student_cannot_retrieve_another_students_log_by_id(self):
        other_log = make_log(self.student2, self.placement2, status="SUBMITTED")

        self._auth(self.student)
        response = self.client.get(f"/api/logs/{other_log.id}/")

        self.assertIn(response.status_code, [403, 404])

    def test_student_cannot_see_evaluations_belonging_to_another_student(self):
        log = make_log(self.student2, self.placement2, status="APPROVED", week_number=1)
        make_evaluation(log, self.academic, self.criteria)

        self._auth(self.student)
        response = self._get("/api/evaluations/")

        self.assertEqual(response.status_code, 403)

        data = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(data), 0)

    def test_workplace_supervisor_cannot_see_unassigned_interns_logs(self):
        supervisor2 = make_supervisor()

        make_log(self.student,  self.placement,  status="SUBMITTED")
        make_log(self.student2, self.placement2, status="SUBMITTED")

        self._auth(supervisor2)
        response = self._get("/api/logs/", {"status": "SUBMITTED", "supervisor": "me"})

        self.assertEqual(response.status_code, 403)

        data = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(data), 0)

