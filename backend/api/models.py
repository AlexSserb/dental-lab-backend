from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

import uuid 


class CustomUserManager(BaseUserManager):
    def create_user(cls, self, email, password, **other_fields):
        email = BaseUserManager.normalize_email(email)
        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, email, password, **other_fields):
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        return self.create_user(self, email, password, **other_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)

    USERNAME_FIELD = "email"
    objects = CustomUserManager()

    def __str__(self):
        return f'{self.email}'


# Справочник видов операций
class OperationType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128)
    exec_time = models.TimeField(auto_now=False, auto_now_add=False)

    def __str__(self):
        return f'{self.name}'


# Справочник видов изделий
class ProductType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128)

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

    def __str__(self):
        return f'{self.name}'


# Статусы операций
class ProductStatus(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128)

    def __str__(self):
        return f'{self.name}'


class OrderStatus(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128)

    def __str__(self):
        return f'{self.name}'


# Заказы
class Order(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    status = models.ForeignKey(OrderStatus, related_name='orders', on_delete=models.CASCADE)
    order_date = models.DateField(auto_now=True)
    discount = models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return f'Заказ для {self.user.last_name} {self.user.first_name}, дата создания: {self.order_date}'


# Изделия
class Product(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    product_type = models.ForeignKey(ProductType, related_name='products', on_delete=models.CASCADE)
    product_status = models.ForeignKey(ProductStatus, related_name='products', on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name='products', on_delete=models.CASCADE)
    amount = models.IntegerField(default=1)

    def __str__(self):
        return f'Изделие "{self.product_type.name}" для заказа от даты {self.order.order_date}'


# Операции
class Operation(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    operation_type = models.ForeignKey(OperationType, related_name='operations', on_delete=models.CASCADE)
    operation_status = models.ForeignKey(OperationStatus, related_name='operations', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='operations', on_delete=models.CASCADE)

    def __str__(self):
        return f'Операция "{self.operation_type.name}" для изделия "{self.product.product_type}" от даты {self.product.order.order_date}'
