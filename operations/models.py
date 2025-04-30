import uuid

import pghistory
from django.db import models
from django.utils import timezone

from orders.models import User
from works.models import WorkType, Work
from core.models import BaseModel


# Create your models here.
class OperationType(BaseModel):
    class OperationGroup(models.TextChoices):
        MODELS = "MO", "Модели"
        CAD_CAM = "CA", "CAD\\CAM"
        CERAMICS = "CE", "Керамика"
        DENTURES = "DE", "Протезы"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(max_length=128, verbose_name="Наименование")
    exec_time = models.TimeField(auto_now=False, auto_now_add=False, verbose_name="Время выполнения")
    group = models.CharField(
        max_length=2,
        choices=OperationGroup.choices,
        default=OperationGroup.MODELS,
        verbose_name="Группа",
    )

    class Meta:
        verbose_name = "Тип операции"
        verbose_name_plural = "Типы операций"

    def get_group(self):
        return self.OperationGroup(self.group).label

    def __str__(self):
        return f"{self.name}, группа: {self.get_group()}"


class WorkTypeOperationType(models.Model):
    work_type = models.ForeignKey(WorkType, on_delete=models.CASCADE, verbose_name="Тип работы")
    operation_type = models.ForeignKey(OperationType, on_delete=models.CASCADE, verbose_name="Тип операции")
    ordinal_number = models.PositiveIntegerField(verbose_name="Порядковый номер выполнения")

    class Meta:
        unique_together = (
            "work_type",
            "ordinal_number",
        )


class OperationStatus(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    number = models.PositiveIntegerField(verbose_name="Номер")
    name = models.CharField(max_length=128, verbose_name="Наименование")

    class Meta:
        verbose_name = "Статус операции"
        verbose_name_plural = "Статусы операций"

    def __str__(self):
        return f"{self.name}"

    @staticmethod
    def get_default_status():
        status = OperationStatus.objects.filter(number=1).first()
        if not status:
            status = OperationStatus.objects.create(name="Default status", number=1)
        return status


class Operation(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    operation_type = models.ForeignKey(OperationType, related_name="operations", on_delete=models.CASCADE,
                                       verbose_name="Тип операции")
    operation_status = models.ForeignKey(OperationStatus, related_name="operations", on_delete=models.CASCADE,
                                         null=True, verbose_name="Статус")
    work = models.ForeignKey(Work, related_name="operations", on_delete=models.CASCADE, verbose_name="Работа")
    tech = models.ForeignKey(User, related_name="operations", null=True, on_delete=models.CASCADE,
                             verbose_name="Техник", blank=True)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")
    ordinal_number = models.PositiveIntegerField(verbose_name="Порядковый номер")
    exec_start = models.DateTimeField(null=True, blank=True, verbose_name="Начало выполнения")
    is_exec_start_editable = models.BooleanField(default=True, verbose_name="Можно ли редактировать время выполнения")

    class Meta:
        verbose_name = "Операция"
        verbose_name_plural = "Операции"
        unique_together = (
            "work",
            "ordinal_number",
        )

    def __str__(self):
        return f'Операция "{self.operation_type.name}" для работы "{self.work.work_type}" от даты {self.work.order.order_date}'


# История изменения статусов операций
BaseOperationEvent = pghistory.create_event_model(Operation, fields=["operation_status"])


class OperationEvent(BaseOperationEvent):
    operation_status = models.ForeignKey(OperationStatus, related_name="history", on_delete=models.CASCADE)
    pgh_obj = models.ForeignKey(Operation, related_name="history", on_delete=models.CASCADE)
