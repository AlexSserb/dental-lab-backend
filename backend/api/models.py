from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

import uuid 


User = get_user_model()

# Справочник видов операций
class OperationType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128)
    exec_time = models.TimeField(auto_now=False, auto_now_add=False)

    class Meta:
        verbose_name = "Тип операции"
        verbose_name_plural = "Типы операций"

    def __str__(self):
        return f'{self.name}'


# Справочник видов изделий
class ProductType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128)
    operation_types = models.ManyToManyField(OperationType, related_name='product_types')

    class Meta:
        verbose_name = "Тип изделия"
        verbose_name_plural = "Типы изделий"

    def __str__(self):
        return f'{self.name}'


# Статусы операций
class OperationStatus(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = "Статус операции"
        verbose_name_plural = "Статусы операций"

    def __str__(self):
        return f'{self.name}'


# Статусы операций
class ProductStatus(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = "Статус изделия"
        verbose_name_plural = "Статусы изделий"

    def __str__(self):
        return f'{self.name}'

    @staticmethod
    def get_default_status():
        return ProductStatus.objects.filter(id='45580d30-0dd4-489d-869f-791bd991b2e5').first()
        if not order_status:
            order_status = OrderStatus.objects.create(id='45580d30-0dd4-489d-869f-791bd991b2e5', 
                name='Отправлено для формирования заказа')
        return order_status


class OrderStatus(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = "Статус заказа"
        verbose_name_plural = "Статусы заказов"

    def __str__(self):
        return f'{self.name}'

    @staticmethod
    def get_default_status():
        order_status = OrderStatus.objects.filter(id='40182114-bf8a-4e78-a5d3-491c778611eb').first()
        if not order_status:
            order_status = OrderStatus.objects.create(id='40182114-bf8a-4e78-a5d3-491c778611eb', 
                name='Отправлено для формирования заказа')
        return order_status


# Заказы
class Order(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    status = models.ForeignKey(OrderStatus, related_name='orders', on_delete=models.CASCADE)
    order_date = models.DateField(auto_now=True)
    discount = models.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f'Заказ для {self.user.last_name} {self.user.first_name}, дата создания: {self.order_date}'


# Изделия
class Product(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    product_type = models.ForeignKey(ProductType, related_name='products', on_delete=models.CASCADE)
    product_status = models.ForeignKey(ProductStatus, related_name='products', on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name='products', on_delete=models.CASCADE)
    amount = models.IntegerField(default=1)

    class Meta:
        verbose_name = "Изделие"
        verbose_name_plural = "Изделия"

    def __str__(self):
        return f'Изделие "{self.product_type.name}" для заказа от даты {self.order.order_date}'

    @staticmethod
    def products_from_product_types(product_types: list[dict], order: Order):
        for product_type in product_types:
            product_type_id = product_type.get("product_type_id", None)
            if not product_type_id:
                print('Не указан тип изделия')
                continue

            product_type_inst = ProductType.objects.filter(id=product_type_id).first()
            if not product_type_inst:
                print('Указан несуществующий тип изделия.')
                continue

            amount = product_type.get("amount", None)
            if not amount:
                print('Не указано количество изделий')
                continue
            
            product = Product.objects.create(product_type=product_type_inst, amount=amount,
                order=order, product_status=ProductStatus.get_default_status())


class Tooth(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    product = models.ForeignKey(Product, related_name='teeth', on_delete=models.CASCADE)
    tooth_number = models.PositiveIntegerField(validators=[MinValueValidator(11), MaxValueValidator(48)])
    
    class Meta:
        verbose_name = "Отмеченный зуб"
        verbose_name_plural = "Отмеченные зубы"

    def __str__(self):
        return f'Зуб под номером {self.tooth_number} для изделия "{self.product.product_type.name}"'


# Операции
class Operation(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    operation_type = models.ForeignKey(OperationType, related_name='operations', on_delete=models.CASCADE)
    operation_status = models.ForeignKey(OperationStatus, related_name='operations', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='operations', on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Операция"
        verbose_name_plural = "Операции"

    def __str__(self):
        return f'Операция "{self.operation_type.name}" для изделия "{self.product.product_type}" от даты {self.product.order.order_date}'
