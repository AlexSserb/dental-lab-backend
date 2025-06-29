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


class WorkType(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128, verbose_name="Наименование")
    operation_types = models.ManyToManyField(
        "operations.OperationType", related_name="work_types", through="operations.WorkTypeOperationType"
    )
    cost = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=2, default=0.0, verbose_name="Цена")

    class Meta:
        verbose_name = "Тип работы"
        verbose_name_plural = "Типы работ"

    def __str__(self):
        return f"{self.name}"


class WorkStatus(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    number = models.PositiveIntegerField(verbose_name="Номер")
    name = models.CharField(max_length=128, verbose_name="Наименование")

    class Meta:
        verbose_name = "Статус работы"
        verbose_name_plural = "Статусы работ"

    def __str__(self):
        return f"{self.name}"

    @staticmethod
    def get_default_status():
        status = WorkStatus.objects.filter(number=1).first()
        if not status:
            status = WorkStatus.objects.create(name="Default status", number=1)
        return status

    @staticmethod
    def get_defect_status():
        status = WorkStatus.objects.filter(number=4).first()
        if not status:
            status = WorkStatus.objects.create(name="Найден дефект", number=4)
        return status


class Work(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    work_type = models.ForeignKey(WorkType, related_name="works", on_delete=models.CASCADE,
                                  verbose_name="Тип работы")
    work_status = models.ForeignKey(WorkStatus, related_name="works", on_delete=models.CASCADE,
                                    verbose_name="Статус")
    order = models.ForeignKey("orders.Order", related_name="works", on_delete=models.CASCADE, verbose_name="Заказ")
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
        verbose_name = "Работа"
        verbose_name_plural = "Работы"

    def __str__(self):
        return (
            f'Работа "{self.work_type.name}" в кол-ве {self.amount} шт. для заказа от даты {self.order.order_date}'
        )

    @staticmethod
    def works_from_work_types(work_types: list[dict], order: "Order"):
        for work_type in work_types:
            work_type_id = work_type.get("work_type_id", None)
            teeth = work_type.get("teeth", None)
            amount = work_type.get("amount", None)

            if work_type_id and amount and teeth and type(teeth) is list:
                work_type_inst = WorkType.objects.filter(id=work_type_id).first()

                if work_type_inst:
                    work = Work.objects.create(
                        work_type=work_type_inst,
                        amount=amount,
                        order=order,
                        work_status=WorkStatus.get_default_status(),
                        teeth=teeth,
                    )
                    work.save()

    def get_discount(self) -> float:
        return max(self.discount, self.order.discount)

    def get_cost(self) -> float:
        return round(
            self.work_type.cost * self.amount * Decimal.from_float(1 - self.get_discount() / 100),
            2,
        )


# История изменения статусов работ
BaseWorkEvent = pghistory.create_event_model(Work, fields=["work_status"])


class WorkEvent(BaseWorkEvent):
    work_status = models.ForeignKey(WorkStatus, related_name="history", on_delete=models.CASCADE)
    pgh_obj = models.ForeignKey(Work, related_name="history", on_delete=models.CASCADE)
