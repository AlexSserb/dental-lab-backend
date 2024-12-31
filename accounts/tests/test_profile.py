from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from django.urls import reverse

from django.contrib.auth.models import Group


class ProfileTest(TestCase):
    """
    Integration tests for profile
    """

    fixtures: list[str] = [
        "./accounts/fixtures/test_data.json",
    ]

    email: str = "alex@mail.com"
    password: str = "12345678sa"
    first_name: str = "Alex"
    last_name: str = "Serb"

    URL: str = "/api/accounts"

    @classmethod
    def setUpTestData(cls):
        cls.user = User(
            id=1, email=cls.email, first_name=cls.first_name, last_name=cls.last_name
        )
        cls.user.set_password(cls.password)
        cls.user.save()
        cls.user.groups.add(1)

        client = APIClient()
        response = client.post(
            cls.URL + "/token/", data={"email": cls.email, "password": cls.password}
        )
        cls.token = response.data["access"]

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

    def test_get_profile_correct(self):
        response = self.client.get(self.URL + f"/profile/{self.email}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.email)
        self.assertEqual(response.data["first_name"], self.first_name)
        self.assertEqual(response.data["last_name"], self.last_name)
        self.assertTrue("password" not in response.data)

    def test_get_profile_user_not_exist(self):
        response = self.client.get(self.URL + "/profile/some_user@mail.com")

        self.assertEqual(response.status_code, 404)

    def test_edit_first_name_correct(self):
        self.first_name = "John"
        response = self.client.patch(
            self.URL + f"/profile/edit-first-name/{self.email}/{self.first_name}",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.email)
        self.assertEqual(response.data["first_name"], self.first_name)
        self.assertEqual(response.data["last_name"], self.last_name)
        self.assertEqual(response.data["group"], "Администратор лаборатории")
        self.assertTrue("password" not in response.data)

    def test_edit_first_name_user_not_exist(self):
        response = self.client.patch(
            self.URL + f"/profile/edit-first-name/some_user@mail.com/Example",
            follow=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_edit_last_name_correct(self):
        self.last_name = "Example"
        response = self.client.patch(
            self.URL + f"/profile/edit-last-name/{self.email}/{self.last_name}",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.email)
        self.assertEqual(response.data["first_name"], self.first_name)
        self.assertEqual(response.data["last_name"], self.last_name)
        self.assertEqual(response.data["group"], "Администратор лаборатории")
        self.assertTrue("password" not in response.data)

    def test_edit_last_name_user_not_exist(self):
        response = self.client.patch(
            self.URL + f"/profile/edit-last-name/some_user@mail.com/Example",
            follow=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_change_password_correct(self):
        new_password = "87654321"
        data = {"old_password": self.password, "new_password": new_password}

        response = self.client.post(self.URL + "/password-change/", data=data)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email=self.email)
        self.assertTrue(user.check_password(new_password))

    def test_change_password_incorrect_old_password(self):
        new_password = "87654321"
        data = {"old_password": "incorrect password", "new_password": new_password}

        response = self.client.post(self.URL + "/password-change/", data=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["old_password"][0], "Wrong password")

    def test_change_password_incorrect_length(self):
        new_password = "123"
        data = {"old_password": self.password, "new_password": new_password}

        response = self.client.post(self.URL + "/password-change/", data=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["new_password"][0].code, "min_length")

    def create_user(
        self,
        id: int,
        email: str,
        group: int,
        first_name: str = "test",
        last_name: str = "test",
        password: str = "test",
    ):
        tech = User(id=id, email=email, first_name=first_name, last_name=last_name)
        tech.set_password(password)
        tech.save()
        tech.groups.add(group)

    def test_get_technicians(self):
        self.create_user(2, "example1@mail.com", 1)
        self.create_user(3, "example2@mail.com", 2)
        self.create_user(4, "example3@mail.com", 2)

        response = self.client.get(self.URL + "/technicians/2", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            set(tech["email"] for tech in response.data),
            {"example2@mail.com", "example3@mail.com"},
        )
