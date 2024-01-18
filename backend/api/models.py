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

    class Meta:
        verbose_name = "Тип изделия"
        verbose_name_plural = "Типы изделий"

    def __str__(self):
        return f'{self.name}'


# Связь многие-ко-многим для видов изделий и соответствующих видов операций
class OperationTypeProductType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    operation_type = models.ForeignKey(OperationType, related_name='product_types', on_delete=models.CASCADE)
    product_type = models.ForeignKey(ProductType, related_name='operation_types', on_delete=models.CASCADE)


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


class OrderStatus(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = "Статус заказа"
        verbose_name_plural = "Статусы заказов"

    def __str__(self):
        return f'{self.name}'


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


class Tooth(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    product = models.ForeignKey(Product, related_name='teeth', on_delete=models.CASCADE)
    is_upper_jaw = models.BooleanField()
    is_right_side = models.BooleanField()
    tooth_number = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    
    class Meta:
        verbose_name = "Отмеченный зуб"
        verbose_name_plural = "Отмеченные зубы"

    def __str__(self):
        jaw = 'верхняя челюсть' if self.is_upper_jaw else 'нижняя челюсть'
        side = 'правая сторона' if self.is_right_side else 'левая сторона'
        return f'Зуб под номером {self.tooth_number}, {jaw}, {side}, для изделия "{self.product.product_type.name}"'


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
