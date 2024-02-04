from django.test import TestCase

from accounts.models import User
from django.urls import reverse


class RegistrationTest(TestCase):
    """
        Integration tests for registration
    """

    URL: str = '/accounts'

    def test_registration_user_correct(self):
        registration_data = {
            'email': 'vasya@mail.com', 
            'password': '12345678sa',
            'first_name': 'MyFirstName',
            'last_name': 'MyLastName'
        }
        response = self.client.post(self.URL + '/register/', data=registration_data)

        self.assertEqual(response.status_code, 200)

        user = User.objects.filter(email=registration_data['email']).first()

        # Checking that the user has been found
        self.assertTrue(user)

        # Checking that the user's fields are saved correctly
        self.assertNotEqual(user.password, registration_data['password'])
        self.assertEqual(user.first_name, registration_data['first_name'])
        self.assertEqual(user.last_name, registration_data['last_name'])
        
        # Checking that access and refresh tokens are in response
        self.assertTrue('access' in response.data)
        self.assertTrue('refresh' in response.data)

    def test_registration_user_without_email(self):
        registration_data = {'password': '12345678sa', 'first_name': 'MyFirstName', 'last_name': 'MyLastName'}
        response = self.client.post(self.URL + '/register/', data=registration_data)

        self.assertEqual(response.status_code, 400)

    def test_registration_user_without_password(self):
        registration_data = {'email': 'vasya@mail.com', 'first_name': 'MyFirstName', 'last_name': 'MyLastName'}
        response = self.client.post(self.URL + '/register/', data=registration_data)

        self.assertEqual(response.status_code, 400)

    def test_registration_users_with_duplicate_emails(self):
        registration_data = {
            'email': 'vasya@mail.com', 
            'password': '12345678sa',
            'first_name': 'MyFirstName',
            'last_name': 'MyLastName'
        }
        # First registration is correct
        response = self.client.post(self.URL + '/register/', data=registration_data)
        self.assertEqual(response.status_code, 200)
        # Second registratin is not correct
        response = self.client.post(self.URL + '/register/', data=registration_data)
        self.assertEqual(response.status_code, 400)
