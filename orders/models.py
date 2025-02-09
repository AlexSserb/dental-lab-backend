import uuid
from decimal import Decimal, getcontext

import pghistory
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from core.models import BaseModel
from products.models import Product

User = get_user_model()

DECIMAL_PRECISION = 9
getcontext().prec = DECIMAL_PRECISION


class OrderStatus(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=128, verbose_name="Наименование")

    class Meta:
        verbose_name = "Статус заказа"
        verbose_name_plural = "Статусы заказов"

    def __str__(self):
        return f"{self.name}"

    @staticmethod
    def get_default_status():
        status = OrderStatus.objects.filter(number=1).first()
        if not status:
            status = OrderStatus.objects.create(name="Default status", number=1)
        return status


class Order(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    user = models.ForeignKey(User, related_name="orders", on_delete=models.CASCADE, verbose_name="Заказчик")
    status = models.ForeignKey(OrderStatus, related_name="orders", on_delete=models.CASCADE, verbose_name="Статус")
    order_date = models.DateField(auto_now_add=True, verbose_name="Дата оформления")
    discount = models.IntegerField(default=0, validators=[MaxValueValidator(100), MinValueValidator(0)],
                                   verbose_name="Скидка")
    comment = models.CharField(default="", max_length=512, verbose_name="Комментарий", blank=True)
    customer = models.ForeignKey("accounts.Customer", related_name="orders", on_delete=models.CASCADE, null=True,
                                 verbose_name="Заказчик")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ для {self.user.last_name} {self.user.first_name}, дата создания: {self.order_date}"

    def get_cost(self) -> float:
        products = Product.objects.filter(order=self).all()
        cost = sum((product.get_cost() for product in products))
        return round(cost, 2)

    def get_cost_with_discount(self) -> float:
        cost = self.get_cost()
        return round(cost * Decimal((1 - self.discount / 100)), 2)


# История изменения статусов заказов
BaseOrderEvent = pghistory.create_event_model(Order, fields=["status"])


class OrderEvent(BaseOrderEvent):
    status = models.ForeignKey(OrderStatus, related_name="history", on_delete=models.CASCADE)
    pgh_obj = models.ForeignKey(Order, related_name="history", on_delete=models.CASCADE)
