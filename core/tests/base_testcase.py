from django.test import TestCase
from datetime import datetime

from rest_framework.test import APIClient


class BaseTestCase(TestCase):
    admin_email = "admin@gmail.com"
    tech_email = "tech1@mail.com"
    physician_email = "doctor1@mail.com"
    password = "12345678"

    url: str = "/api"

    fixtures: list[str] = [
        "./accounts/fixtures/test_data/groups.json",
        "./accounts/fixtures/test_data/customers.json",
        "./accounts/fixtures/test_data/users.json",

        "./core/fixtures/test_data/statuses.json",
        "./core/fixtures/test_data/object_types.json",
        "./core/fixtures/test_data/orders.json",
        "./core/fixtures/test_data/works.json",
        "./core/fixtures/test_data/operations.json",
    ]

    @classmethod
    def setUpTestData(cls):
        curr_date = datetime.now()
        cls.year = curr_date.year
        cls.month = curr_date.month

        client = APIClient()
        token_endpoint = "/api/accounts/token/"
        response = client.post(token_endpoint, data={"email": cls.admin_email, "password": cls.password})
        cls.admin_token = response.data["access"]

        response = client.post(token_endpoint, data={"email": cls.physician_email, "password": cls.password})
        cls.physician_token = response.data["access"]

        response = client.post(token_endpoint, data={"email": cls.tech_email, "password": cls.password})
        cls.tech_token = response.data["access"]

    def set_up_for_physician(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.physician_token)

    def set_up_for_admin(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_token)

    def set_up_for_tech(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.tech_token)
