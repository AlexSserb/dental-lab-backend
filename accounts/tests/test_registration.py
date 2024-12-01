from django.test import TestCase

from accounts.models import User, Customer
from django.urls import reverse


class RegistrationTest(TestCase):
    """
    Integration tests for registration
    """

    fixtures: list[str] = [
        "./accounts/fixtures/test_data.json",
    ]

    URL: str = "/api/accounts"

    def test_registration_user_correct(self):
        registration_data = {
            "email": "vasya@mail.com",
            "password": "12345678sa",
            "first_name": "MyFirstName",
            "last_name": "MyLastName",
            "customers": [
                "3b1479eb-306c-44f7-926f-ef9fb1530d25",
                "a2203146-68ba-411f-ba45-815a52ef7236",
            ],
        }
        response = self.client.post(self.URL + "/register/", data=registration_data)

        self.assertEqual(response.status_code, 200)

        user = User.objects.get(email=registration_data["email"])

        # Checking that the user has been found
        self.assertTrue(user)

        # Checking that the user's fields are saved correctly
        self.assertNotEqual(user.password, registration_data["password"])
        self.assertEqual(user.first_name, registration_data["first_name"])
        self.assertEqual(user.last_name, registration_data["last_name"])
        self.assertEqual(len(user.customers.all()), 2)

        # Checking that access and refresh tokens are in response
        self.assertTrue("access" in response.data)
        self.assertTrue("refresh" in response.data)

    def test_registration_user_without_email(self):
        registration_data = {
            "password": "12345678sa",
            "first_name": "MyFirstName",
            "last_name": "MyLastName",
        }
        response = self.client.post(self.URL + "/register/", data=registration_data)

        self.assertEqual(response.status_code, 400)

    def test_registration_user_without_password(self):
        registration_data = {
            "email": "vasya@mail.com",
            "first_name": "MyFirstName",
            "last_name": "MyLastName",
        }
        response = self.client.post(self.URL + "/register/", data=registration_data)

        self.assertEqual(response.status_code, 400)

    def test_registration_users_with_duplicate_emails(self):
        registration_data = {
            "email": "vasya@mail.com",
            "password": "12345678sa",
            "first_name": "MyFirstName",
            "last_name": "MyLastName",
        }
        # First registration is correct
        response = self.client.post(self.URL + "/register/", data=registration_data)
        self.assertEqual(response.status_code, 200)
        # Second registratin is not correct
        response = self.client.post(self.URL + "/register/", data=registration_data)
        self.assertEqual(response.status_code, 400)
