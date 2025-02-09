from rest_framework.test import APIClient

from accounts.tests.base_testcase import BaseAccountsTestCase


class TechniciansTest(BaseAccountsTestCase):

    @classmethod
    def setUpTestData(cls):
        client = APIClient()
        response = client.post(cls.URL + "/token/", data={"email": cls.email, "password": cls.password})
        cls.token = response.data["access"]

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

    def test_get_technicians_by_id(self):
        response = self.client.get(self.URL + "/technicians/5")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], "tech3@mail.com")
