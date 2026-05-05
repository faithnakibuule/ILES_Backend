from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from placements.models import Company, InternshipPlacement
from logbook.models import WeeklyLog
from reviews.models import Notification

User = get_user_model()

class PlacementPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_superuser(
            email = 'admin@test.com', password = 'adminpass', role = 'admin'
        )
        self.student = User.objects.create_user(
            email = 'student@test.com', password = 'studentpass', role = 'student'
        )
        self.student2 = User.objects.create_user(
            email = 'student2@test.com', password = 'studentpass2', role = 'student'
        )
        self.company = Company.objects.create(name="Test Company")
        self.supervisor = User.objects.create_user(
            email = 'supervisor@test.com',
            password = 'supervisorpass',
            role = 'workplace_supervisor',
            company = self.company,
        )
        self.academic = User.objects.create_user(
            email='academic@test.com',
            password='academicpass',
            role='academic_supervisor'
        )

    def test_student_cannot_create_placement(self):
        self.client.force_authenticate(user = self.student)
        response = self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_id": self.company.id,
            "company_name": "Hacker Corp",
            "start_date": "2026-06-01",
            "end_date": "2026-08-31",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_companies_can_be_listed_without_authentication(self):
        response = self.client.get('/api/placements/companies/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data['results']
        self.assertEqual(results[0]['name'], "Test Company")
            
    def test_admin_can_create_placement(self):
        self.client.force_authenticate(user = self.admin)
        response = self.client.post('/api/placements/',{
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "academic_supervisor_id": self.academic.id,
            "company_id": self.company.id,
            "start_date": "2026-06-01",
            "end_date": "2026-08-31",
            "status": "ACTIVE",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_can_only_see_own_placement(self):
        self.client.force_authenticate(user = self.student)
        response = self.client.get('/api/placements/')

        if isinstance(response.data, list):
            placements = response.data
        else:
            placements = response.data['results']
        for placement in placements:
            self.assertEqual(placement['student']['id'], self.student.id)

    def test_date_validation_rejects_invalid_range(self):
        self.client.force_authenticate(user = self.admin)
        response = self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_id": self.company.id,
            "start_date": "2026-08-31",
            "end_date": "2026-06-01",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    
    def test_admin_can_create_placement(self):
            self.client.force_authenticate(user=self.admin)
            response = self.client.post('/api/placements/',{
                "student_id": self.student.id,
                "workplace_supervisor_id": self.supervisor.id,
                "company_id": self.company.id,
                "start_date": "2026-06-01",
                "end_date": "2026-08-31",
                "status": "ACTIVE",
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_cannot_create_placement(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_id": self.company.id,
            "start_date": "2026-06-01",
            "end_date": "2026-08-31",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_student_in_creation(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/placements/', {
            # student_id omitted
            "workplace_supervisor_id": self.supervisor.id,
            "company_id": self.company.id,
            "start_date": "2026-06-01",
            "end_date": "2026-08-31",
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unassigned_supervisor_returns_validation_error(self):
        self.client.force_authenticate(user=self.admin)
        unassigned_supervisor = User.objects.create_user(
            email='unassigned-supervisor@test.com',
            password='supervisorpass',
            role='workplace_supervisor',
        )

        response = self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": unassigned_supervisor.id,
            "company_id": self.company.id,
            "start_date": "2026-06-01",
            "end_date": "2026-08-31",
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_update_status_transition(self):
        # Admin creates a placement
        self.client.force_authenticate(user=self.admin)
        post = self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_id": self.company.id,
            "start_date": "2026-01-01",
            "end_date": "2026-06-01",
        }, format='json')
        placement_id = post.data['id']
        # Admin updates status to ACTIVE
        response = self.client.patch(f'/api/placements/{placement_id}/', {"status": "ACTIVE"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], "ACTIVE")

    def test_student_cannot_receive_second_active_or_completed_placement(self):
        # Admin creates first placement
        self.client.force_authenticate(user=self.admin)
        self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_id": self.company.id,
            "start_date": "2026-01-01",
            "end_date": "2026-03-01",
            "status": "ACTIVE",
        }, format='json')
        second_company = Company.objects.create(name="Second Company")
        second_supervisor = User.objects.create_user(
            email='supervisor2@test.com',
            password='supervisorpass2',
            role='workplace_supervisor',
            company=second_company,
        )
        response = self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": second_supervisor.id,
            "company_id": second_company.id,
            "start_date": "2026-02-01",
            "end_date": "2026-04-01",
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_cancel_placement_with_confirmation(self):
        self.client.force_authenticate(user=self.admin)
        create_response = self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_id": self.company.id,
            "start_date": "2026-01-01",
            "end_date": "2026-03-01",
            "status": "ACTIVE",
        }, format='json')
        placement_id = create_response.data['id']
        placement = InternshipPlacement.objects.get(pk=placement_id)

        WeeklyLog.objects.create(
            intern=self.student,
            placement=placement,
            week_number=1,
            activities='Testing',
            learning_points='Validation',
        )

        denied = self.client.post(
            f'/api/placements/{placement_id}/cancel/',
            {},
            format='json',
        )
        self.assertEqual(denied.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            f'/api/placements/{placement_id}/cancel/',
            {"confirm": True},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        placement.refresh_from_db()
        self.assertEqual(placement.status, 'CANCELLED')
        self.assertFalse(WeeklyLog.objects.filter(placement=placement).exists())
 
