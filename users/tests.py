from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import CustomUser

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

    def test_register_with_mismatched_passwords_returns_400(self):
        data = {
            "email": "student2@test.com",
            "password": "StrongPass123!",
            "confirm_password": "WrongPass999!",
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