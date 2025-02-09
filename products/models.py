import uuid
from decimal import Decimal, getcontext
from typing import TYPE_CHECKING

import pghistory
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import BaseModel

if TYPE_CHECKING:
    from orders.models import Order

DECIMAL_PRECISION = 9
getcontext().prec = DECIMAL_PRECISION


def get_default_product_info():
    return dict.fromkeys(("title", "description"), "")


class ProductType(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128, verbose_name="Наименование")
    operation_types = models.ManyToManyField(
        "operations.OperationType", related_name="product_types", through="operations.ProductTypeOperationType"
    )
    cost = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=2, default=0.0, verbose_name="Цена")

    class Meta:
        verbose_name = "Тип изделия"
        verbose_name_plural = "Типы изделий"

    def __str__(self):
        return f"{self.name}"


class ProductStatus(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    number = models.PositiveIntegerField(verbose_name="Номер")
    name = models.CharField(max_length=128, verbose_name="Наименование")

    class Meta:
        verbose_name = "Статус изделия"
        verbose_name_plural = "Статусы изделий"

    def __str__(self):
        return f"{self.name}"

    @staticmethod
    def get_default_status():
        status = ProductStatus.objects.filter(number=1).first()
        if not status:
            status = ProductStatus.objects.create(name="Default status", number=1)
        return status


class Product(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    product_type = models.ForeignKey(ProductType, related_name="products", on_delete=models.CASCADE,
                                     verbose_name="Тип изделия")
    product_status = models.ForeignKey(ProductStatus, related_name="products", on_delete=models.CASCADE,
                                       verbose_name="Статус")
    order = models.ForeignKey("orders.Order", related_name="products", on_delete=models.CASCADE, verbose_name="Заказ")
    amount = models.IntegerField(default=1, verbose_name="Количество")
    discount = models.IntegerField(default=0, validators=[MaxValueValidator(100), MinValueValidator(0)],
                                   verbose_name="Скидка")
    teeth = ArrayField(
        models.IntegerField(validators=[MinValueValidator(11), MaxValueValidator(48)]),
        default=list,
        verbose_name="Номера зубов",
        blank=True,
    )

    class Meta:
        verbose_name = "Изделие"
        verbose_name_plural = "Изделия"

    def __str__(self):
        return (
            f'Изделие "{self.product_type.name}" в кол-ве {self.amount} шт. для заказа от даты {self.order.order_date}'
        )

    @staticmethod
    def products_from_product_types(product_types: list[dict], order: "Order"):
        for product_type in product_types:
            product_type_id = product_type.get("product_type_id", None)
            teeth = product_type.get("teeth", None)
            amount = product_type.get("amount", None)

            if product_type_id and amount and teeth and type(teeth) is list:
                product_type_inst = ProductType.objects.filter(id=product_type_id).first()

                if product_type_inst:
                    product = Product.objects.create(
                        product_type=product_type_inst,
                        amount=amount,
                        order=order,
                        product_status=ProductStatus.get_default_status(),
                        teeth=teeth,
                    )

    def get_discount(self):
        return max(self.discount, self.order.discount)

    def get_cost(self):
        return round(
            self.product_type.cost * self.amount * Decimal.from_float(1 - self.get_discount() / 100),
            2,
        )


# История изменения статусов изделий
BaseProductEvent = pghistory.create_event_model(Product, fields=["product_status"])


class ProductEvent(BaseProductEvent):
    product_status = models.ForeignKey(ProductStatus, related_name="history", on_delete=models.CASCADE)
    pgh_obj = models.ForeignKey(Product, related_name="history", on_delete=models.CASCADE)
