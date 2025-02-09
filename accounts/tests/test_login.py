import jwt

from accounts.tests.base_testcase import BaseAccountsTestCase


class LoginTest(BaseAccountsTestCase):

    email_doctor = "doctor1@mail.com"

    def login_test(self, email: str, expected_group_id: int, expected_group_name: str):
        response = self.client.post(
            self.URL + "/token/",
            data={"email": email, "password": self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        decoded = jwt.decode(
            response.data["access"], verify=False, options={"verify_signature": False}
        )
        self.assertEqual(decoded["groupId"], expected_group_id)
        self.assertEqual(decoded["group"], expected_group_name)

    def test_login_doctor_correct(self):
        self.login_test(self.email_doctor, 0, "Врач")

    def test_login_admin_correct(self):
        self.login_test(self.email, 1, "Администратор лаборатории")

    def test_login_incorrect_password(self):
        response = self.client.post(
            self.URL + "/token/",
            data={"email": self.email_doctor, "password": "incorrect password"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertTrue("access" not in response.data)
