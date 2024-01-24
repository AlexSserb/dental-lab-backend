from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from django.urls import reverse

from django.contrib.auth.models import Group


class ProfileViewTest(TestCase):
    """
        Testing view for profile data
    """

    email = 'alex@mail.com'
    password = '12345678sa'
    first_name = 'Alex'
    last_name = 'Serb'
    URL = '/accounts'

    @classmethod
    def setUpTestData(cls):
        group_dir = Group(name='Director')
        group_dir.save()
        group_admin = Group(name='Lab admin')
        group_admin.save()

        user = User(id=1, email=cls.email, first_name=cls.first_name, last_name=cls.last_name)
        user.set_password(cls.password)
        user.save()
        user.groups.add(group_dir)

    def setUp(self):
        response = self.client.post(self.URL + '/token/', data={'email': self.email, 'password': self.password})
        self.token = response.data['access']

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
