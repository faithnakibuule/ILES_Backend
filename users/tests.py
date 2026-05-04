from django.test import TestCase
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from users.models import Course, CustomUser

class AuthAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'

    def test_register_with_valid_data_returns_201(self):
        data = {
            "email": "student1@test.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "role": "student"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_student_with_course_name_creates_course(self):
        data = {
            "email": "student-course@test.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "role": "student",
            "course_name": "Bachelor of Software Engineering",
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Course.objects.filter(name="Bachelor of Software Engineering").exists()
        )

    def test_courses_can_be_listed_without_authentication(self):
        Course.objects.create(name="Computer Science")

        response = self.client.get('/api/courses/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data['results']
        self.assertEqual(results[0]['name'], "Computer Science")

    def test_register_with_mismatched_passwords_returns_400(self):
        data = {
            "email": "student2@test.com",
            "password": "StrongPass123!",
            "confirm_password": "WrongPass999!",
            "role": "student"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
    # Create a user with the email
        CustomUser.objects.create_user(
            email="student2@test.com",
            password="StrongPass123",
            role="student"
        )

        data = {
            "email": "student2@test.com",  # SAME email now ✅
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
            "role": "student"
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        
    def test_login_with_wrong_password_returns_401(self):
        CustomUser.objects.create_user(
            email="realuser@test.com",
            password="CorrectPass123!",
            role="student"
        )
        data = {
            "email": "realuser@test.com",
            "password": "WrongPassword!"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_returns_tokens_and_user_context(self):
        CustomUser.objects.create_user(
            email="frontend@test.com",
            password="CorrectPass123!",
            role="student",
            first_name="Front",
            last_name="End",
        )

        response = self.client.post(self.login_url, {
            "email": "frontend@test.com",
            "password": "CorrectPass123!",
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['role'], "student")
        self.assertEqual(response.data['full_name'], "Front End")
        self.assertEqual(response.data['user']['email'], "frontend@test.com")
        
    def test_me_requires_authentication(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)    
        
    def test_me_returns_user_data_when_authenticated(self):
        user = CustomUser.objects.create_user(
            email="me@test.com",
            password="StrongPass123!",
            role="student"
        )

        # Log in to get token
        login_response = self.client.post('/api/auth/login/', {
            "email": "me@test.com",
            "password": "StrongPass123!"
        }, format='json')

        token = login_response.data['access']

        # Attach token to request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get('/api/auth/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], "me@test.com")
        self.assertIn('fullname', response.data)
        self.assertIn('full_name', response.data)
        
        
    def test_token_refresh_returns_new_access_token(self):
        user = CustomUser.objects.create_user(
            email="refresh@test.com",
            password="StrongPass123!",
            role="student"
        )

        # Login to get tokens
        login_response = self.client.post('/api/auth/login/', {
            "email": "refresh@test.com",
            "password": "StrongPass123!"
        }, format='json')

        refresh_token = login_response.data['refresh']

        # Request new access token
        response = self.client.post('/api/auth/token/refresh/', {
            "refresh": refresh_token
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)    
        
    def test_token_refresh_with_invalid_token_returns_401(self):
        response = self.client.post('/api/auth/token/refresh/', {
            "refresh": "invalidtoken123"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)    


class CourseAdminAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.courses_url = '/api/courses/'
        self.admin = CustomUser.objects.create_user(
            email="admin@test.com",
            password="StrongPass123!",
            role="admin",
        )
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            password="StrongPass123!",
            role="student",
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_admin_can_create_course_for_student_registration(self):
        self.authenticate(self.admin)

        response = self.client.post(
            self.courses_url,
            {"name": "Bachelor of Information Technology"},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Bachelor of Information Technology")
        self.assertTrue(
            Course.objects.filter(name="Bachelor of Information Technology").exists()
        )

    def test_admin_can_update_course_name(self):
        course = Course.objects.create(name="Computer Science")
        self.authenticate(self.admin)

        response = self.client.patch(
            f"{self.courses_url}{course.id}/",
            {"name": "Applied Computer Science"},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course.refresh_from_db()
        self.assertEqual(course.name, "Applied Computer Science")

    def test_admin_can_delete_course(self):
        course = Course.objects.create(name="Software Engineering")
        self.authenticate(self.admin)

        response = self.client.delete(f"{self.courses_url}{course.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Course.objects.filter(id=course.id).exists())

    def test_student_cannot_create_course(self):
        self.authenticate(self.student)

        response = self.client.post(
            self.courses_url,
            {"name": "Cybersecurity"},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Course.objects.filter(name="Cybersecurity").exists())

    def test_course_list_includes_admin_created_courses_for_registration(self):
        Course.objects.create(name="Data Science")
        Course.objects.create(name="Software Engineering")

        response = self.client.get(self.courses_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data['results']
        self.assertEqual(
            [course["name"] for course in results],
            ["Data Science", "Software Engineering"],
        )


class PasswordResetAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email="resetme@test.com",
            password="StrongPass123!",
            role="student",
            first_name="Reset",
            last_name="User",
        )

    @override_settings(FRONTEND_URL="http://localhost:5173")
    @patch("users.email_utils.send_mail")
    def test_password_reset_request_sends_email_with_frontend_link(self, mock_send_mail):
        response = self.client.post(
            "/api/auth/password_reset/",
            {"email": "resetme@test.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_mail.assert_called_once()
        self.assertIn("/reset-password?uid=", mock_send_mail.call_args.kwargs["message"])

    def test_password_reset_confirm_updates_password(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            "/api/auth/password_reset/confirm/",
            {
                "uid": uid,
                "token": token,
                "new_password": "NewStrongPass123!",
                "new_password_confirm": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass123!"))
