from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from django.urls import reverse

from django.contrib.auth.models import Group


class ProfileTest(TestCase):
    """
        Integration tests for profile
    """
    fixtures: list[str] = ['./accounts/fixtures/test_data.json',]

    email: str = 'alex@mail.com'
    password: str = '12345678sa'
    first_name: str = 'Alex'
    last_name: str = 'Serb'

    URL: str = '/accounts'

    @classmethod
    def setUpTestData(cls):
        user = User(id=1, email=cls.email, first_name=cls.first_name, last_name=cls.last_name)
        user.set_password(cls.password)
        user.save()
        user.groups.add(1)

        client = APIClient()
        response = client.post('/accounts/token/', data={'email': cls.email, 'password': cls.password})
        cls.token = response.data['access']

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_get_profile_correct(self):
        # the profile data is obtained by token
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = client.get(self.URL + '/profile/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], self.email)
        self.assertEqual(response.data['first_name'], self.first_name)
        self.assertEqual(response.data['last_name'], self.last_name)
        self.assertTrue('password' not in response.data)
        
    def test_get_profile_incorrect_token(self):
        # the profile data is obtained by token
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token + '1')
        response = client.get(self.URL + '/profile/')

        self.assertEqual(response.status_code, 401)