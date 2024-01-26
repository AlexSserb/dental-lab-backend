from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import Group
from datetime import datetime

from accounts.models import User
from api.models import *


class ViewsTest(TestCase):
    """
        Testing views for api
    """
    fixtures = ['./api/fixtures/groups_data.json', './api/fixtures/test_data_statuses.json',
        './api/fixtures/operation_and_product_types.json']

    email = 'alex@mail.com'
    password = '12345678sa'
    first_name = 'Alex'
    last_name = 'Serb'
    URL = '/api'

    @classmethod
    def setUpTestData(cls):
        cls.user = User(id=1, email=cls.email, first_name=cls.first_name, last_name=cls.last_name)
        cls.user.set_password(cls.password)
        cls.user.save()
        cls.user.groups.add(Group.objects.filter(name="Director").first().id)

    def setUp(self):
        response = self.client.post('/accounts/token/', data={'email': self.email, 'password': self.password})
        self.token = response.data['access']

    def test_get_orders_correct(self):
        order = Order.objects.create(user=self.user, discount=0.05,
            status=OrderStatus.objects.filter(name="At work").first()).save()
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = client.get(self.URL + '/orders/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status']['name'], 'At work')
        self.assertEqual(response.data[0]['order_date'], datetime.now().strftime('%Y-%m-%d'))
        self.assertEqual(response.data[0]['discount'], '0.05')
        
    def test_get_orders_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token + '1')
        response = client.get(self.URL + '/orders/')

        self.assertEqual(response.status_code, 401)
