from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import Group
from datetime import datetime
from uuid import uuid4

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
            status=OrderStatus.objects.filter(name="At work").first())
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = client.get(self.URL + '/orders/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        response_order = response.data[0]
        self.assertEqual(response_order['status']['name'], 'At work')
        self.assertEqual(response_order['order_date'], datetime.now().strftime('%Y-%m-%d'))
        self.assertEqual(response_order['discount'], '0.05')
        
    def test_get_orders_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token + '1')
        response = client.get(self.URL + '/orders/')

        self.assertEqual(response.status_code, 401)

    def test_get_products_for_order_correct(self):
        order = Order.objects.create(user=self.user, discount=0.05,
            status=OrderStatus.objects.filter(name='At work').first())

        product1 = Product.objects.create(product_status=ProductStatus.objects.filter(name='A defect was found').first(),
            product_type=ProductType.objects.filter(name='Product type 2').first(), order=order, amount=2)
        product2 = Product.objects.create(product_status=ProductStatus.objects.filter(name='Ready').first(),
            product_type=ProductType.objects.filter(name='Product type 1').first(), order=order, amount=1)

        tooth1 = Tooth.objects.create(product=product1, tooth_number=13)
        tooth2 = Tooth.objects.create(product=product1, tooth_number=12)
        tooth3 = Tooth.objects.create(product=product2, tooth_number=25)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = client.get(self.URL + '/products/' + str(order.id), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        # Check first product
        self.assertEqual(response.data[0]['product_status']['name'], 'A defect was found')
        self.assertEqual(response.data[0]['product_type']['name'], 'Product type 2')
        self.assertEqual(len(response.data[0]['teeth']), 2)
        # Check second product 
        self.assertEqual(response.data[1]['product_status']['name'], 'Ready')
        self.assertEqual(response.data[1]['product_type']['name'], 'Product type 1')
        self.assertEqual(len(response.data[1]['teeth']), 1)
        self.assertEqual(response.data[1]['teeth'][0]['tooth_number'], 25)
        
    def test_get_products_for_order_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token + '1')
        response = client.get(self.URL + '/products/123', follow=True)

        self.assertEqual(response.status_code, 401)
