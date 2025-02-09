from rest_framework.test import APIClient

from accounts.tests.base_testcase import BaseAccountsTestCase


class CustomersTest(BaseAccountsTestCase):

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

    def test_get_all_customers(self):
        client = APIClient()
        response = client.get(self.URL + "/customers/")

        self.assertEqual(response.status_code, 200)
        customers = response.data
        self.assertEqual(len(customers), 2)
        self.assertEqual(
            {c["phone_number"] for c in customers},
            {"88005553535", "88003333333"},
        )
        self.assertEqual(
            {c["created_at"] for c in customers},
            {"2024-08-15", "2024-07-25"},
        )

    def test_attach_customers_to_users(self):
        data = {
            "customers": [
                "a2203146-68ba-411f-ba45-815a52ef7236",
                "3b1479eb-306c-44f7-926f-ef9fb1530d25",
            ]
        }
        response = self.client.post(self.URL + "/customers/attach", data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["customers"]), 2)
