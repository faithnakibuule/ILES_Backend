from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class HealthAPITests(TestCase):
    def test_health_endpoint_is_public(self):
        response = APIClient().get('/api/health/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
