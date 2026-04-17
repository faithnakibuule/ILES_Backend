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