from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User


class TechniciansTest(TestCase):
    """
    Integration tests for technicians
    """

    fixtures: list[str] = [
        "./accounts/fixtures/test_data.json",
    ]

    email: str = "alex@mail.com"
    password: str = "12345678sa"
    first_name: str = "Alex"
    last_name: str = "Serb"

    URL: str = "/accounts"

    @classmethod
    def add_user(cls, id, email, first_name, last_name, password, group):
        user = User(id=id, email=email, first_name=first_name, last_name=last_name)
        user.set_password(password)
        user.groups.add(group)
        user.save()

    @classmethod
    def setUpTestData(cls):
        cls.add_user(1, cls.email, cls.first_name, cls.last_name, cls.password, 2)
        cls.add_user(2, "2@mail.com", "FN2", "LN2", "12345678", 6)
        cls.add_user(3, "3@mail.com", "LN3", "LN3", "12345678", 7)

        client = APIClient()
        response = client.post(cls.URL + "/token/", data={"email": cls.email, "password": cls.password})
        cls.token = response.data["access"]

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

    def test_get_technicians_by_id(self):
        response = self.client.get(self.URL + "/technicians/6")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], "2@mail.com")
