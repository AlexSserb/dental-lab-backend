from accounts.models import User
from orders.models import *
from core.tests import BaseTestCase
from works.models import WorkStatus, Work


class OrdersTest(BaseTestCase):
    url = "/api/orders"

    def test_get_orders_correct(self):
        self.set_up_for_admin()
        response = self.client.get(self.url + f"/orders/2025/1", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        response_order = response.data[0]
        self.assertEqual(response_order["status"]["name"], "В работе")
        self.assertEqual(response_order["order_date"], "2025-01-02")
        self.assertEqual(response_order["discount"], 5)

        response_order = response.data[1]
        self.assertEqual(response_order["status"]["name"], "Готов")
        self.assertEqual(response_order["order_date"], "2025-01-02")
        self.assertEqual(response_order["discount"], 10)

    def test_get_orders_for_physician_correct(self):
        self.set_up_for_physician()
        response = self.client.get(self.url + "/orders-for-physician", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(
            {order["id"] for order in response.data["results"]},
            {"68eb5be8-d29f-4a6c-ac64-5be9740fb3f3", "c5f7d483-347b-4cbb-93b2-f9de7cd03cc9"}
        )

    def test_create_order(self):
        self.set_up_for_physician()
        data = {
            "customer_id": "a2203146-68ba-411f-ba45-815a52ef7236",
            "work_types": [
                {
                    "work_type_id": "00be8d3f-a127-4de3-a1b7-1c5d093c2ae7",
                    "amount": 4,
                    "teeth": [11, 12, 22, 31],
                },
                {
                    "work_type_id": "d4e1e752-5c18-490d-99d4-0b606e50c938",
                    "amount": 2,
                    "teeth": [45, 46],
                },
            ],
        }

        response = self.client.post(self.url + "/create-order/", data=data, format="json")

        self.assertEqual(response.status_code, 200)

        user = User.objects.get(email=self.physician_email)
        order = Order.objects.filter(user=user).latest("order_date")
        self.assertEqual(order.discount, 0)
        self.assertEqual(order.status.name, OrderStatus.get_default_status().name)
        self.assertEqual(order.customer.name, "Городская стоматология №1")

        works = order.works.all()
        work1, work2 = self.check_works_created_correctly(works)

        self.assertEqual(set(work1.teeth), {11, 12, 22, 31})
        self.assertEqual(set(work2.teeth), {45, 46})

    def check_works_created_correctly(self, works: list[Work]) -> tuple:
        self.assertEqual(len(works), 2)
        work1, work2 = (
            (works[0], works[1]) if works[0].amount == 4 else (works[1], works[0])
        )
        self.assertEqual(work1.work_type.name, "Изделие 2")
        self.assertEqual(work2.work_type.name, "Изделие 1")
        self.assertEqual(work2.amount, 2)
        self.assertEqual(
            work1.work_status.name, WorkStatus.get_default_status().name
        )
        self.assertEqual(work1.work_status.name, work2.work_status.name)
        return work1, work2

    def test_create_order_incorrect_data(self):
        # Incorrect data: tooth number 90 is not correct
        self.set_up_for_physician()
        data = {
            "customer_id": "a2203146-68ba-411f-ba45-815a52ef7236",
            "work_types": [
                {
                    "work_type_id": "00be8d3f-a127-4de3-a1b7-1c5d093c2ae7",
                    "amount": 2,
                    "teeth": [90, 46],
                },
            ],
        }

        response = self.client.post(self.url + "/create-order/", data=data, format="json")

        self.assertEqual(response.status_code, 400)

    def test_order_get_cost(self):
        order = Order.objects.get(id="c5f7d483-347b-4cbb-93b2-f9de7cd03cc9")
        work1, work2 = order.works.all()

        self.assertEqual(order.get_cost(), Decimal("71575.00"))
        self.assertEqual(order.get_cost_with_discount(), Decimal("64417.50"))

        order.discount = 0
        order.save()
        work1.discount = 0
        work1.save()
        work2.discount = 0
        work2.save()
        self.assertEqual(order.get_cost_with_discount(), Decimal("82000.00"))

    def test_confirm_order(self):
        self.set_up_for_admin()

        work1_id = "60b5e09a-9d70-486e-a010-64f3504ce0a9"
        work2_id = "8186b733-ff3f-4e28-8361-9701cb63e5e5"

        test_data = {
            "works_discounts_data": [
                {"id": work1_id, "discount": 12},
                {"id": work2_id, "discount": 6},
            ],
            "order_discount_data": {"id": "c5f7d483-347b-4cbb-93b2-f9de7cd03cc9", "discount": 10},
        }

        response = self.client.post(self.url + f"/confirm-order/", data=test_data, format="json")

        work1 = Work.objects.get(id=work1_id)
        work2 = Work.objects.get(id=work2_id)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["discount"] == 10)
        self.assertEqual(response.data["status"]["name"], OrderStatus.objects.get(number=2).name)
        self.assertTrue(work1.discount == 12)
        self.assertTrue(work2.discount == 6)
        self.assertTrue(work1.work_status.name == work2.work_status.name)
        self.assertTrue(work2.work_status.name, "Готово")
