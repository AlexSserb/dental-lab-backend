from datetime import datetime

import pytz
from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from orders.models import *


class OperationsTest(TestCase):
    """
    Integration tests for operations and dental technicians
    """

    fixtures: list[str] = [
        "./orders/fixtures/groups_data.json",
        "./orders/fixtures/test_data_statuses.json",
        "./orders/fixtures/operation_and_product_types.json",
    ]

    tech_email: str = "alex@mail.com"
    admin_email: str = "admin@mail.com"
    password: str = "12345678sa"
    first_name: str = "Alex"
    last_name: str = "Serb"
    URL: str = "/api/orders"

    @classmethod
    def create_user(cls, user_id: int, email: str, group: int) -> User:
        user = User(
            id=user_id, email=email, first_name=cls.first_name, last_name=cls.last_name
        )
        user.set_password(cls.password)
        user.save()
        user.groups.add(group)
        return user

    @classmethod
    def setUpTestData(cls):
        cls.tech = cls.create_user(1, cls.tech_email, 2)
        cls.admin = cls.create_user(2, cls.admin_email, 1)

        client = APIClient()
        token_endpoint = "/api/accounts/token/"
        response = client.post(token_endpoint, data={"email": cls.tech_email, "password": cls.password})
        cls.tech_token = response.data["access"]

        response = client.post(token_endpoint, data={"email": cls.admin_email, "password": cls.password})
        cls.admin_token = response.data["access"]

    def set_up_for_tech(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.tech_token)

    def set_up_for_admin(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_token)

    def test_get_operations_for_tech_correct(self):
        # region set test data
        self.set_up_for_tech()
        order = Order.objects.create(
            user=self.tech, discount=0.05, status=OrderStatus.objects.get(number=3)
        )
        product = Product.objects.create(
            product_status=ProductStatus.objects.get(number=3),
            product_type=ProductType.objects.get(name="Product type 2"),
            order=order,
            amount=2,
        )

        operation_status = OperationStatus.objects.get(number=2)
        operation1 = Operation.objects.create(
            product=product,
            tech=self.tech,
            operation_status=operation_status,
            operation_type=OperationType.objects.get(name="Operation type 3"),
            ordinal_number=1,
        )
        operation2 = Operation.objects.create(
            product=product,
            tech=self.tech,
            operation_status=operation_status,
            operation_type=OperationType.objects.get(name="Operation type 2"),
            ordinal_number=2,
        )
        # endregion

        response = self.client.get(self.URL + "/operations-for-tech/")
        self.assertEqual(response.status_code, 200)
        resp: list = response.data["results"]

        self.assertEqual(len(resp), 2)
        if resp[0]["operation_type"]["name"] != "Operation type 3":
            resp[0], resp[1] = resp[1], resp[0]
        self.assertTrue(
            resp[0]["operation_status"]["name"]
            == resp[1]["operation_status"]["name"]
            == "At work"
        )
        self.assertEqual(resp[0]["operation_type"]["name"], "Operation type 3")
        self.assertEqual(resp[1]["operation_type"]["name"], "Operation type 2")
        self.assertTrue(
            resp[0]["product"]["product_type"]["name"]
            == resp[1]["product"]["product_type"]["name"]
            == "Product type 2"
        )

    def test_get_operations_for_tech_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + self.tech_token + "1")
        response = client.get(self.URL + "/operations-for-tech/")

        self.assertEqual(response.status_code, 401)

    def test_get_operations_for_product_correct(self):
        # region set test data
        self.set_up_for_admin()
        order = Order.objects.create(
            user=self.tech, discount=0.05, status=OrderStatus.objects.get(number=3)
        )
        product1 = Product.objects.create(
            product_status=ProductStatus.objects.get(number=3),
            product_type=ProductType.objects.get(name="Product type 2"),
            order=order,
            amount=2,
        )
        product2 = Product.objects.create(
            product_status=ProductStatus.objects.get(number=2),
            product_type=ProductType.objects.get(name="Product type 1"),
            order=order,
            amount=5,
        )

        operation_status = OperationStatus.objects.get(number=2)
        operation1 = Operation.objects.create(
            product=product1,
            tech=self.tech,
            operation_status=operation_status,
            operation_type=OperationType.objects.get(name="Operation type 3"),
            ordinal_number=1,
        )
        operation2 = Operation.objects.create(
            product=product2,
            tech=self.tech,
            operation_status=operation_status,
            operation_type=OperationType.objects.get(name="Operation type 2"),
            ordinal_number=2,
        )
        # endregion

        response = self.client.get(self.URL + f"/operations-for-product/{product2.id}/")
        resp: list = response.data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(resp), 1)
        self.assertEqual(resp[0]["operation_status"]["number"], 2)
        self.assertEqual(resp[0]["operation_type"]["name"], "Operation type 2")
        self.assertEqual(len(resp[0]["history"]), 1)
        self.assertEqual(resp[0]["history"][0]["operation_status"]["number"], 2)

    def test_get_operations_for_product_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + self.tech_token + "1")
        response = client.get(self.URL + "/operations-for-product/1/")

        self.assertEqual(response.status_code, 401)

    def test_set_operation_status_correct(self):
        # region set test data
        self.set_up_for_tech()
        order = Order.objects.create(
            user=self.tech, discount=0, status=OrderStatus.objects.get(number=3)
        )
        product = Product.objects.create(
            product_status=ProductStatus.objects.get(number=3),
            product_type=ProductType.objects.get(name="Product type 2"),
            order=order,
            amount=1,
        )

        operation = Operation.objects.create(
            product=product,
            tech=self.tech,
            operation_status=OperationStatus.objects.get(number=2),
            operation_type=OperationType.objects.get(name="Operation type 3"),
            ordinal_number=1,
        )
        # endregion

        response = self.client.patch(
            self.URL + f"/operation/{operation.id}/",
            data={"status": "efee01cc-e81b-4936-8580-33e778ae0f67"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["operation_type"]["name"], "Operation type 3")
        self.assertEqual(response.data["operation_status"]["name"], "Ready")

    def test_set_operation_status_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + self.tech_token + "1")
        response = client.patch(
            self.URL + f"/operation/1", data={"status": 123}, follow=True
        )

        self.assertEqual(response.status_code, 401)

    def test_set_operation_status_incorrect_operation_id(self):
        self.set_up_for_tech()

        response = self.client.patch(
            self.URL + f"/operation/6acfbcb5-66eb-460b-a9c9-52a26b1b3461/",
            data={"status": "efee01cc-e81b-4936-8580-33e778ae0f67"},
            follow=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_get_all_operation_statuses_correct(self):
        self.set_up_for_tech()

        response = self.client.get(self.URL + "/operation-statuses/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(
            set(st["name"] for st in response.data),
            {"The work has not started", "At work", "Ready"},
        )

    def test_get_all_operation_statuses_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + self.tech_token + "1")
        response = client.get(self.URL + "/operation-statuses/")

        self.assertEqual(response.status_code, 401)

    def test_get_operations_for_schedule_correct(self):
        # region set test data
        self.set_up_for_tech()
        order = Order.objects.create(
            user=self.tech, discount=0.05, status=OrderStatus.objects.get(number=3)
        )
        product1 = Product.objects.create(
            product_status=ProductStatus.objects.get(number=3),
            product_type=ProductType.objects.get(name="Product type 2"),
            order=order,
            amount=2,
        )
        product2 = Product.objects.create(
            product_status=ProductStatus.objects.get(number=2),
            product_type=ProductType.objects.get(name="Product type 1"),
            order=order,
            amount=5,
        )

        operation_status = OperationStatus.objects.get(number=2)
        operation1 = Operation.objects.create(
            product=product1,
            tech=self.tech,
            operation_status=operation_status,
            operation_type=OperationType.objects.get(name="Operation type 3"),
            exec_start=datetime(
                2024, 3, 25, 16, 25, 0, tzinfo=pytz.timezone(settings.TIME_ZONE)
            ),
            ordinal_number=1,
        )
        operation2 = Operation.objects.create(
            product=product2,
            tech=self.tech,
            operation_status=operation_status,
            operation_type=OperationType.objects.get(name="Operation type 2"),
            exec_start=datetime(
                2024, 3, 29, 11, 10, 0, tzinfo=pytz.timezone(settings.TIME_ZONE)
            ),
            ordinal_number=2,
        )
        # endregion

        response = self.client.get(
            self.URL + f"/operations-for-schedule/{self.tech.email}/2024-03-25"
        )
        resp: list = response.data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(resp), 2)
        self.assertEqual(resp[0]["operation_status"]["number"], 2)
        datetime_pattern = "%Y-%m-%dT%H:%M:%SZ"
        self.assertEqual(
            datetime.strptime(resp[0]["start"], datetime_pattern),
            datetime(2024, 3, 25, 16, 25, 0),
        )
        self.assertEqual(
            datetime.strptime(resp[0]["end"], datetime_pattern),
            datetime(2024, 3, 25, 17, 0, 0),
        )
        self.assertEqual(
            datetime.strptime(resp[1]["start"], datetime_pattern),
            datetime(2024, 3, 29, 11, 10, 0),
        )
        self.assertEqual(
            datetime.strptime(resp[1]["end"], datetime_pattern),
            datetime(2024, 3, 29, 12, 10, 0),
        )

    def test_get_operations_for_schedule_incorrect_token(self):
        self.set_up_for_tech()

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + self.tech_token + "1")
        response = client.get(
            self.URL + f"/operations-for-schedule/{self.tech.email}/2024-03-25"
        )

        self.assertEqual(response.status_code, 401)

    def test_get_products_with_operations_correct(self):
        self.set_up_for_admin()
        order = Order.objects.create(
            user=self.tech, discount=0.05, status=OrderStatus.objects.get(number=3)
        )
        product1 = Product.objects.create(
            product_status=ProductStatus.objects.get(number=3),
            product_type=ProductType.objects.get(name="Product type 2"),
            order=order,
            amount=2,
        )
        product2 = Product.objects.create(
            product_status=ProductStatus.objects.get(number=2),
            product_type=ProductType.objects.get(name="Product type 1"),
            order=order,
            amount=5,
        )

        response = self.client.get(
            self.URL + f"/products/operations/{order.id}", follow=True
        )
        resp: list = response.data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(resp), 2)

        self.assertEqual(resp[0]["product_type"]["name"], "Product type 2")
        self.assertEqual(len(resp[0]["operations"]), 2)
        self.assertEqual(
            set(oper["operation_type"]["name"] for oper in resp[0]["operations"]),
            {"Operation type 2", "Operation type 3"},
        )

        self.assertEqual(resp[1]["product_type"]["name"], "Product type 1")
        self.assertEqual(len(resp[1]["operations"]), 2)
        self.assertEqual(
            set(oper["operation_type"]["name"] for oper in resp[1]["operations"]),
            {"Operation type 1", "Operation type 2"},
        )

    def test_assign_operation_correct(self):
        self.set_up_for_admin()
        order = Order.objects.create(
            user=self.tech, discount=0.05, status=OrderStatus.objects.get(number=3)
        )
        product = Product.objects.create(
            product_status=ProductStatus.objects.get(number=3),
            product_type=ProductType.objects.get(name="Product type 2"),
            order=order,
            amount=2,
        )

        operation = Operation.objects.create(
            product=product,
            operation_status=OperationStatus.objects.get(number=2),
            operation_type=OperationType.objects.get(name="Operation type 3"),
            ordinal_number=1,
        )

        test_data = {
            "id": operation.id,
            "execStart": "2024-04-02T16:08:00.000Z",
            "techEmail": self.tech.email,
        }

        response = self.client.patch(
            self.URL + f"/assign-operation/", data=test_data, format="json"
        )

        self.assertEqual(response.status_code, 200)
        operation = Operation.objects.get(id=operation.id)
        self.assertEqual(operation.tech.email, self.tech.email)
        self.assertEqual(operation.exec_start.year, 2024)
        self.assertEqual(operation.exec_start.month, 4)
