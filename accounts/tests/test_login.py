from django.test import TestCase
from django.urls import reverse
import jwt

from accounts.models import User


class LoginTest(TestCase):
    """
    Integration tests for login and obtaining tokens
    """

    fixtures: list[str] = [
        "./accounts/fixtures/test_data.json",
    ]

    user1_psw = "12345678"
    user2_psw = "87654321"

    URL: str = "/api/accounts"

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User(
            id=1, email="u1@mail.com", first_name="first1", last_name="last1"
        )
        cls.user1.set_password(cls.user1_psw)
        cls.user1.save()
        cls.user1.groups.add(1)

        cls.user2 = User(
            id=2, email="u2@mail.com", first_name="first2", last_name="last2"
        )
        cls.user2.set_password(cls.user2_psw)
        cls.user2.save()

    def test_login_physician_correct(self):
        response = self.client.post(
            self.URL + "/token/",
            data={"email": self.user2.email, "password": self.user2_psw},
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue("access" in response.data)
        self.assertTrue("refresh" in response.data)

        decoded = jwt.decode(
            response.data["access"], verify=False, options={"verify_signature": False}
        )
        self.assertEqual(decoded["groupId"], 0)
        self.assertEqual(decoded["group"], "Врач")

    def test_login_director_correct(self):
        response = self.client.post(
            self.URL + "/token/",
            data={"email": self.user1.email, "password": self.user1_psw},
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue("access" in response.data)
        self.assertTrue("refresh" in response.data)

        decoded = jwt.decode(
            response.data["access"], verify=False, options={"verify_signature": False}
        )
        self.assertEqual(decoded["groupId"], 1)
        self.assertEqual(decoded["group"], "Директор")
