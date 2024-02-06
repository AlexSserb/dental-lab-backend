from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import Group
from django.core.serializers import serialize
from datetime import datetime
from uuid import uuid4

from accounts.models import User
from api.models import *


class OrdersTest(TestCase):
    """
        Integration tests for orders and products
    """
    fixtures: list[str] = ['./api/fixtures/groups_data.json', './api/fixtures/test_data_statuses.json',
        './api/fixtures/operation_and_product_types.json']

    email: str = 'alex@mail.com'
    password: str = '12345678sa'
    first_name: str = 'Alex'
    last_name: str = 'Serb'
    URL: str = '/api'

    @classmethod
    def setUpTestData(cls):
        cls.user = User(id=1, email=cls.email, first_name=cls.first_name, last_name=cls.last_name)
        cls.user.set_password(cls.password)
        cls.user.save()
        cls.user.groups.add(1)

    def setUp(self):
        response = self.client.post('/accounts/token/', data={'email': self.email, 'password': self.password})
        self.token = response.data['access']
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_get_orders_correct(self):
        order = Order.objects.create(user=self.user, discount=0.05,
            status=OrderStatus.objects.get(name="At work"))
        
        response = self.client.get(self.URL + '/orders/')

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
            status=OrderStatus.objects.get(name='At work'))

        product1 = Product.objects.create(product_status=ProductStatus.objects.get(name='A defect was found'),
            product_type=ProductType.objects.get(name='Product type 2'), order=order, amount=2)
        product2 = Product.objects.create(product_status=ProductStatus.objects.get(name='Ready'),
            product_type=ProductType.objects.get(name='Product type 1'), order=order, amount=1)

        tooth1 = Tooth.objects.create(product=product1, tooth_number=13)
        tooth2 = Tooth.objects.create(product=product1, tooth_number=12)
        tooth3 = Tooth.objects.create(product=product2, tooth_number=25)
        
        response = self.client.get(self.URL + '/products/' + str(order.id), follow=True)

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

    def test_create_order(self):
        product_types_data = { 'product_types' : [
            { 'product_type_id': 'a038f028-cfda-4e8b-b971-44cf7d5b84ae', 'amount': 4, 'teeth': [11, 12, 22, 31] },
            { 'product_type_id': '6622d6e9-b655-4894-acab-885bf17fa6a7', 'amount': 2, 'teeth': [45, 46] },
        ]}
        
        response = self.client.post(self.URL + '/create_order/', data=product_types_data, format='json')
        
        self.assertEqual(response.status_code, 200)

        # Check that order created correctly
        orders = Order.objects.filter(user=self.user).all()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].discount, 0)
        self.assertEqual(orders[0].status.name, OrderStatus.get_default_status().name)

		# Check that products created correctly
        products = orders[0].products.all()
        self.assertEqual(len(products), 2)
        product1, product2 = (products[0], products[1]) if \
            products[0].amount == 4 else (products[1], products[0])
        self.assertEqual(product1.product_type.name, 'Product type 1')
        self.assertEqual(product2.product_type.name, 'Product type 2')
        self.assertEqual(product2.amount, 2)
        self.assertEqual(product1.product_status.name, ProductStatus.get_default_status().name)
        self.assertEqual(product1.product_status.name, product2.product_status.name)
		
        teeth_nums = set(tooth.tooth_number for tooth in Tooth.objects.filter(product=product1))
        self.assertEqual(teeth_nums, set((11, 12, 22, 31)))
        teeth_nums = set(tooth.tooth_number for tooth in Tooth.objects.filter(product=product2))
        self.assertEqual(teeth_nums, set((45, 46)))
        
    def test_create_order_incorrect_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token + '1')
        response = client.post(self.URL + '/create_order/')

        self.assertEqual(response.status_code, 401)

    def test_create_order_incorrect_data(self):
        # Incorrect data => tooth number 90 is not correct
        product_types_data = { 'product_types' : [
            { 'product_type_id': '6622d6e9-b655-4894-acab-885bf17fa6a7', 'amount': 2, 'teeth': [90, 46] },
        ]}

        response = self.client.post(self.URL + '/create_order/', data=product_types_data, format='json')

        self.assertEqual(response.status_code, 400)
