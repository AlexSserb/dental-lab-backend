from django.test import TestCase


class BaseTestCase(TestCase):
    email = "admin@gmail.com"
    password = "12345678"
    first_name = "AdminFirstName"
    last_name = "AdminLastName"

    URL: str = "/api/accounts"

    fixtures: list[str] = [
        "./accounts/fixtures/test_data/groups.json",
        "./accounts/fixtures/test_data/customers.json",
        "./accounts/fixtures/test_data/users.json",
    ]
