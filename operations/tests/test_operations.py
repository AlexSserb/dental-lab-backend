from datetime import datetime

from rest_framework.test import APIClient

from core.tests import BaseTestCase
from operations.models import Operation


class OperationsTest(BaseTestCase):
    url = "/api/operations"

    def test_get_operations_for_tech_correct(self):
        self.set_up_for_tech()

        response = self.client.get(self.url + "/operations-for-tech/")
        self.assertEqual(response.status_code, 200)
        resp: list = response.data["results"]

        self.assertEqual(len(resp), 1)
        self.assertTrue(resp[0]["operation_status"]["name"] == "В работе")
        self.assertEqual(resp[0]["operation_type"]["name"], "Операция 2")
        self.assertTrue(resp[0]["product"]["product_type"]["name"] == "Изделие 2")

    def test_get_operations_for_tech_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + self.tech_token + "1")
        response = client.get(self.url + "/operations-for-tech/")

        self.assertEqual(response.status_code, 401)

    def test_get_operations_for_product_correct(self):
        self.set_up_for_admin()

        response = self.client.get(self.url + f"/operations-for-product/60b5e09a-9d70-486e-a010-64f3504ce0a9/")
        resp: list = response.data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(resp), 2)
        self.assertEqual(resp[0]["operation_status"]["number"], 3)
        self.assertEqual(resp[0]["operation_type"]["name"], "Операция 1")
        self.assertEqual(len(resp[0]["history"]), 1)
        self.assertEqual(resp[0]["history"][0]["operation_status"]["number"], 3)

    def test_set_operation_status_correct(self):
        self.set_up_for_tech()

        response = self.client.patch(
            self.url + f"/operation/519beb85-e9a9-43a3-a753-16ed36d4de48/",
            data={"status": "d36c536b-7c07-495c-a34e-8cb0a5ccc3f1"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["operation_type"]["name"], "Операция 2")
        self.assertEqual(response.data["operation_status"]["name"], "В работе")

    def test_set_operation_status_incorrect_operation_id(self):
        self.set_up_for_tech()

        response = self.client.patch(
            self.url + f"/operation/6acfbcb5-66eb-460b-a9c9-52a26b1b3461/",
            data={"status": "efee01cc-e81b-4936-8580-33e778ae0f67"},
            follow=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_get_all_operation_statuses_correct(self):
        self.set_up_for_tech()

        response = self.client.get(self.url + "/operation-statuses/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(
            {st["name"] for st in response.data},
            {"Работа не начата", "В работе", "Готово"},
        )

    def test_get_operations_for_schedule_correct(self):
        self.set_up_for_tech()

        response = self.client.get(self.url + f"/operations-for-schedule/tech2@mail.com/2024-03-25")
        resp: list = response.data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(resp), 2)
        self.assertEqual(resp[0]["operation_status"]["number"], 3)
        datetime_pattern = "%Y-%m-%dT%H:%M:%SZ"
        resp.sort(key=lambda x: x["start"])
        self.assertEqual(
            datetime.strptime(resp[0]["start"], datetime_pattern),
            datetime(2024, 3, 25, 16, 25, 0),
        )
        self.assertEqual(
            datetime.strptime(resp[0]["end"], datetime_pattern),
            datetime(2024, 3, 25, 17, 35, 0),
        )
        self.assertEqual(
            datetime.strptime(resp[1]["start"], datetime_pattern),
            datetime(2024, 3, 29, 11, 10, 0),
        )
        self.assertEqual(
            datetime.strptime(resp[1]["end"], datetime_pattern),
            datetime(2024, 3, 29, 11, 55, 0),
        )

    def test_assign_operation_correct(self):
        self.set_up_for_admin()
        operation_id, tech_email = "9c891983-7afc-41bf-aef4-e2e532743abd", "tech3@mail.com"

        test_data = {
            "id": operation_id,
            "execStart": "2024-04-02T16:08:00.000Z",
            "techEmail": tech_email,
        }

        response = self.client.patch(
            self.url + f"/assign-operation/", data=test_data, format="json"
        )

        self.assertEqual(response.status_code, 200)
        operation = Operation.objects.get(id=operation_id)
        self.assertEqual(operation.tech.email, tech_email)
        self.assertEqual(operation.exec_start.year, 2024)
        self.assertEqual(operation.exec_start.month, 4)
