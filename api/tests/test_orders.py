from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import Group
from django.core.serializers import serialize
from datetime import datetime
from uuid import uuid4
from decimal import Decimal

from accounts.models import User
from api.models import *
from api.serializers import OrderSerializer


class OrdersTest(TestCase):
    """
    Integration tests for orders and products
    """

    fixtures: list[str] = [
        "./api/fixtures/groups_data.json",
        "./api/fixtures/test_data_statuses.json",
        "./api/fixtures/operation_and_product_types.json",
    ]

    email: str = "alex@mail.com"
    password: str = "12345678sa"
    first_name: str = "Alex"
    last_name: str = "Serb"
    URL: str = "/api"

    @classmethod
    def setUpTestData(cls):
        curr_date = datetime.now()
        cls.year = curr_date.year
        cls.month = curr_date.month

        cls.user = User(
            id=1, email=cls.email, first_name=cls.first_name, last_name=cls.last_name
        )
        cls.user.set_password(cls.password)
        cls.user.save()
        cls.user.groups.add(1)

        client = APIClient()
        response = client.post(
            "/accounts/token/", data={"email": cls.email, "password": cls.password}
        )
        cls.token = response.data["access"]

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

    def test_get_orders_correct(self):
        order = Order.objects.create(
            user=self.user, discount=5, status=OrderStatus.objects.get(number=3)
        )

        response = self.client.get(
            self.URL + f"/orders/{self.year}/{self.month}", follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        response_order = response.data[0]
        self.assertEqual(response_order["status"]["name"], "At work")
        self.assertEqual(
            response_order["order_date"], datetime.now().strftime("%Y-%m-%d")
        )
        self.assertEqual(response_order["discount"], 5)

    def test_get_orders_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token + "1")
        response = client.get(
            self.URL + f"/orders/{self.year}/{self.month}", follow=True
        )

        self.assertEqual(response.status_code, 401)

    def test_get_orders_for_physician_correct(self):
        user = User(
            id=2, email="example@mail.com", first_name="First", last_name="Last"
        )
        user.set_password("psw")
        user.save()

        # Order for new user
        order1 = Order.objects.create(
            user=user, discount=5, status=OrderStatus.objects.get(number=3)
        )
        # Order for main user
        order2 = Order.objects.create(
            user=self.user, discount=10, status=OrderStatus.objects.get(number=1)
        )

        response = self.client.get(self.URL + "/orders-for-physician", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], str(order2.id))

    def test_get_orders_for_physician_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token + "1")
        response = client.get(
            self.URL + f"/orders/{self.year}/{self.month}", follow=True
        )

        self.assertEqual(response.status_code, 401)

    def test_get_products_for_order_correct(self):
        order = Order.objects.create(
            user=self.user, discount=5, status=OrderStatus.objects.get(number=3)
        )

        product1 = Product.objects.create(
            product_status=ProductStatus.objects.get(number=3),
            product_type=ProductType.objects.get(name="Product type 2"),
            order=order,
            amount=2,
            teeth=[12, 13],
        )
        product2 = Product.objects.create(
            product_status=ProductStatus.objects.get(number=4),
            product_type=ProductType.objects.get(name="Product type 1"),
            order=order,
            amount=1,
            teeth=[25],
        )

        response = self.client.get(self.URL + f"/products/{order.id}", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        # Check first product
        self.assertEqual(
            response.data[0]["product_status"]["name"], "A defect was found"
        )
        self.assertEqual(response.data[0]["product_type"]["name"], "Product type 2")
        self.assertEqual(set(response.data[0]["teeth"]), set((12, 13)))
        # Check second product
        self.assertEqual(response.data[1]["product_status"]["name"], "Ready")
        self.assertEqual(response.data[1]["product_type"]["name"], "Product type 1")
        self.assertEqual(len(response.data[1]["teeth"]), 1)
        self.assertEqual(response.data[1]["teeth"][0], 25)

    def test_get_products_for_order_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token + "1")
        response = client.get(self.URL + "/products/123", follow=True)

        self.assertEqual(response.status_code, 401)

    def test_create_order(self):
        product_types_data = {
            "product_types": [
                {
                    "product_type_id": "a038f028-cfda-4e8b-b971-44cf7d5b84ae",
                    "amount": 4,
                    "teeth": [11, 12, 22, 31],
                },
                {
                    "product_type_id": "6622d6e9-b655-4894-acab-885bf17fa6a7",
                    "amount": 2,
                    "teeth": [45, 46],
                },
            ]
        }

        response = self.client.post(
            self.URL + "/create-order/", data=product_types_data, format="json"
        )

        self.assertEqual(response.status_code, 200)

        # Check that order created correctly
        orders = Order.objects.filter(user=self.user).all()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].discount, 0)
        self.assertEqual(orders[0].status.name, OrderStatus.get_default_status().name)

        products = orders[0].products.all()
        product1, product2 = self.check_products_created_correctly(products)

        # Check teeth marks created correctly
        self.assertEqual(set(product1.teeth), set((11, 12, 22, 31)))
        self.assertEqual(set(product2.teeth), set((45, 46)))

    def check_products_created_correctly(self, products: list[Product]) -> tuple:
        self.assertEqual(len(products), 2)
        product1, product2 = (
            (products[0], products[1])
            if products[0].amount == 4
            else (products[1], products[0])
        )
        self.assertEqual(product1.product_type.name, "Product type 1")
        self.assertEqual(product2.product_type.name, "Product type 2")
        self.assertEqual(product2.amount, 2)
        self.assertEqual(
            product1.product_status.name, ProductStatus.get_default_status().name
        )
        self.assertEqual(product1.product_status.name, product2.product_status.name)
        return product1, product2

    def test_create_order_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token + "1")
        response = client.post(self.URL + "/create-order/")

        self.assertEqual(response.status_code, 401)

    def test_create_order_incorrect_data(self):
        # Incorrect data => tooth number 90 is not correct
        product_types_data = {
            "product_types": [
                {
                    "product_type_id": "6622d6e9-b655-4894-acab-885bf17fa6a7",
                    "amount": 2,
                    "teeth": [90, 46],
                },
            ]
        }

        response = self.client.post(
            self.URL + "/create-order/", data=product_types_data, format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_order_get_cost(self):
        order = Order.objects.create(
            user=self.user, status=OrderStatus.objects.get(number=3)
        )

        product1 = Product.objects.create(
            product_status=ProductStatus.objects.get(number=3),
            product_type=ProductType.objects.get(name="Product type 2"),
            order=order,
            amount=2,
        )
        product2 = Product.objects.create(
            product_status=ProductStatus.objects.get(number=4),
            product_type=ProductType.objects.get(name="Product type 1"),
            order=order,
            amount=5,
        )

        order.discount = 9
        self.assertEqual(order.get_cost(), Decimal("154804.30"))
        self.assertEqual(order.get_cost_with_discount(), Decimal("140871.91"))

        product1.discount = 1
        product1.save()
        product2.discount = 3
        product2.save()
        self.assertEqual(order.get_cost_with_discount(), Decimal("137606.73"))

    def test_confirm_order(self):
        order = Order.objects.create(
            user=self.user, status=OrderStatus.get_default_status()
        )

        product_default_status = ProductStatus.get_default_status()
        product1 = Product.objects.create(
            product_status=product_default_status,
            product_type=ProductType.objects.get(name="Product type 2"),
            order=order,
            amount=2,
        )
        product2 = Product.objects.create(
            product_status=product_default_status,
            product_type=ProductType.objects.get(name="Product type 1"),
            order=order,
            amount=5,
        )

        test_data = {
            "products": [
                {"id": product1.id, "discount": 12},
                {"id": product2.id, "discount": 6},
            ],
            "order": {"id": order.id, "discount": 10},
        }

        response = self.client.post(
            self.URL + f"/confirm-order/", data=test_data, format="json"
        )

        product1 = Product.objects.get(id=product1.id)
        product2 = Product.objects.get(id=product2.id)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["discount"] == 10)
        self.assertEqual(
            response.data["status"]["name"], OrderStatus.objects.get(number=2).name
        )
        self.assertTrue(product1.discount == 12)
        self.assertTrue(product2.discount == 6)
        self.assertTrue(product1.product_status.name == product2.product_status.name)
        self.assertTrue(
            product2.product_status.name == ProductStatus.objects.get(number=2).name
        )
