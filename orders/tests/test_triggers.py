from django.test import TestCase

from accounts.models import User
from orders.models import *


class TriggersTest(TestCase):

    fixtures: list[str] = [
        "./orders/fixtures/test_data/statuses.json",
        "./orders/fixtures/test_data/object_types.json",
    ]

    URL: str = "/api/orders"

    @classmethod
    def setUpTestData(cls):
        user = User(id=1, email="email@mail.com", first_name="A", last_name="B")
        user.set_password("1111111")
        user.save()

        cls.order = Order.objects.create(
            user=user, discount=0, status=OrderStatus.get_default_status()
        )
        cls.product = Product.objects.create(
            product_status=ProductStatus.get_default_status(),
            product_type=ProductType.objects.get(name="Изделие 2"),
            order=cls.order,
            amount=1,
        )

        cls.operation = Operation.objects.create(
            product=cls.product,
            tech=user,
            ordinal_number=1,
            operation_status=OperationStatus.get_default_status(),
            operation_type=OperationType.objects.get(name="Операция 3"),
        )

    def test_order_history_trigger(self):
        order_history = OrderEvent.objects.filter(pgh_obj_id=self.order.id).all()

        self.assertEqual(len(order_history), 1)
        self.assertEqual(order_history[0].status.name, "Отправлено для формирования наряда")

        # Change status
        self.order.status = OrderStatus.objects.get(number=3)
        self.order.save()

        # The order history changes due to a change in the order status
        order_history = (
            OrderEvent.objects.filter(pgh_obj_id=self.order.id)
            .order_by("pgh_created_at")
            .all()
        )
        self.assertEqual(len(order_history), 2)
        self.assertEqual(order_history[1].status.name, "В работе")

    def test_product_history_trigger(self):
        product_history = ProductEvent.objects.filter(pgh_obj_id=self.product.id).all()

        self.assertEqual(len(product_history), 1)
        self.assertEqual(product_history[0].product_status.name, "Работа не начата")

        # Change status
        self.product.product_status = ProductStatus.objects.get(number=3)
        self.product.save()

        # The order history changes due to a change in the order status
        product_history = (
            ProductEvent.objects.filter(pgh_obj_id=self.product.id)
            .order_by("pgh_created_at")
            .all()
        )
        self.assertEqual(len(product_history), 2)
        self.assertEqual(product_history[1].product_status.name, "Готово")

    def test_operation_history_trigger(self):
        operation_history = OperationEvent.objects.filter(
            pgh_obj_id=self.operation.id
        ).all()

        self.assertEqual(len(operation_history), 1)
        self.assertEqual(
            operation_history[0].operation_status.name, "Работа не начата"
        )

        # Change status
        self.operation.operation_status = OperationStatus.objects.get(number=2)
        self.operation.save()

        # The order history changes due to a change in the order status
        operation_history = (
            OperationEvent.objects.filter(pgh_obj_id=self.operation.id)
            .order_by("pgh_created_at")
            .all()
        )
        self.assertEqual(len(operation_history), 2)
        self.assertEqual(operation_history[1].operation_status.name, "В работе")
