from core.tests import BaseTestCase


class ProductsTest(BaseTestCase):
    url = "/api/products"

    def test_get_products_for_order_correct(self):
        self.set_up_for_admin()
        response = self.client.get(self.url + f"/c5f7d483-347b-4cbb-93b2-f9de7cd03cc9", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        # Check first product
        self.assertEqual(response.data[0]["product_status"]["name"], "Готово")
        self.assertEqual(response.data[0]["product_type"]["name"], "Изделие 3")
        self.assertEqual(set(response.data[0]["teeth"]), {12, 13})
        # Check second product
        self.assertEqual(response.data[1]["product_status"]["name"], "Готово")
        self.assertEqual(response.data[1]["product_type"]["name"], "Изделие 2")
        self.assertEqual(set(response.data[1]["teeth"]), {25})

    def test_get_products_with_operations_correct(self):
        self.set_up_for_admin()

        response = self.client.get(
            self.url + f"/operations/c5f7d483-347b-4cbb-93b2-f9de7cd03cc9", follow=True
        )
        resp: list = response.data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(resp), 2)

        self.assertEqual(resp[0]["product_type"]["name"], "Изделие 3")
        self.assertEqual(len(resp[0]["operations"]), 2)
        self.assertEqual(
            {oper["operation_type"]["name"] for oper in resp[0]["operations"]},
            {"Операция 1", "Операция 2"},
        )

        self.assertEqual(resp[1]["product_type"]["name"], "Изделие 2")
        self.assertEqual(len(resp[1]["operations"]), 0)
