from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from placements.models import InternshipPlacement
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
        self.supervisor = User.objects.create_user(
            email = 'supervisor@test.com', password = 'supervisorpass', role = 'workplace_supervisor'
        )

    def test_student_cannot_create_placement(self):
        self.client.force_authenticate(user = self.student)
        response = self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_name": "Hacker Corp",
            "start_date": "2026-06-01",
            "end_date": "2026-08-31",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            
    def test_admin_can_create_placement(self):
        self.client.force_authenticate(user = self.admin)
        response = self.client.post('/api/placements/',{
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_name": "Good Corp",
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
            self.assertEqual(placement['student'], self.student.id)

    def test_date_validation_rejects_invalid_range(self):
        self.client.force_authenticate(user = self.admin)
        response = self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_name": "Bad Corp",
            "start_date": "2026-08-31",
            "end_date": "2026-06-01",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    
    def test_admin_can_create_placement(self):
            self.client.force_authenticate(user=self.admin)
            response = self.client.post('/api/placements/',{
                "student_id": self.student.id,
                "workplace_supervisor_id": self.supervisor.id,
                "company_name": "Good Corp",
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
            "company_name": "Hacker Corp",
            "start_date": "2026-06-01",
            "end_date": "2026-08-31",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_student_in_creation(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/placements/', {
            # student_id omitted
            "workplace_supervisor_id": self.supervisor.id,
            "company_name": "NoStudent Corp",
            "start_date": "2026-06-01",
            "end_date": "2026-08-31",
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_status_transition(self):
        # Admin creates a placement
        self.client.force_authenticate(user=self.admin)
        post = self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_name": "Status Corp",
            "start_date": "2026-01-01",
            "end_date": "2026-06-01",
        }, format='json')
        placement_id = post.data['id']
        # Admin updates status to ACTIVE
        response = self.client.patch(f'/api/placements/{placement_id}/', {"status": "ACTIVE"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], "ACTIVE")

    def test_overlapping_placements_allowed(self):
        # Admin creates first placement
        self.client.force_authenticate(user=self.admin)
        self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_name": "Overlap Corp 1",
            "start_date": "2026-01-01",
            "end_date": "2026-03-01",
        }, format='json')
        # Create overlapping placement (no validation in code, so expect success)
        response = self.client.post('/api/placements/', {
            "student_id": self.student.id,
            "workplace_supervisor_id": self.supervisor.id,
            "company_name": "Overlap Corp 2",
            "start_date": "2026-02-01",
            "end_date": "2026-04-01",
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
 