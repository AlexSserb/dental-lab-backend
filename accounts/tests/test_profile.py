from rest_framework.test import APIClient

from accounts.models import User
from accounts.tests.base_testcase import BaseTestCase


class ProfileTest(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
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

    def check_profile_data(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.email)
        self.assertEqual(response.data["first_name"], self.first_name)
        self.assertEqual(response.data["last_name"], self.last_name)
        self.assertEqual(response.data["group"], "Администратор лаборатории")
        self.assertTrue("password" not in response.data)

    def test_edit_first_name_correct(self):
        self.first_name = "John"
        response = self.client.patch(
            self.URL + f"/profile/edit-first-name/{self.email}/{self.first_name}",
            follow=True,
        )

        self.check_profile_data(response)

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

        self.check_profile_data(response)

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

    def test_get_technicians(self):
        response = self.client.get(self.URL + "/technicians/2", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], "tech1@mail.com")
