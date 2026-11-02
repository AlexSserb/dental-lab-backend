import uuid

from django.conf import settings
from django.db import models

from core.models import BaseModel


class LlmCallLog(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Время вызова")
    feature = models.CharField(max_length=64, db_index=True, verbose_name="Функция")
    model = models.CharField(max_length=128, verbose_name="Модель")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="llm_calls", verbose_name="Пользователь",
    )
    prompt_tokens = models.PositiveIntegerField(default=0, verbose_name="Токены запроса")
    completion_tokens = models.PositiveIntegerField(default=0, verbose_name="Токены ответа")
    attempts = models.PositiveSmallIntegerField(default=1, verbose_name="Попытки")
    latency = models.FloatField(default=0, verbose_name="Задержка, с")
    cost = models.DecimalField(max_digits=12, decimal_places=6, default=0, verbose_name="Стоимость, USD")
    success = models.BooleanField(default=False, verbose_name="Успешно")
    error = models.CharField(max_length=512, blank=True, default="", verbose_name="Ошибка")

    class Meta:
        verbose_name = "Лог вызова LLM"
        verbose_name_plural = "Логи вызова LLM"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.feature} {self.model} {'ok' if self.success else 'fail'}"

    @property
    def tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens
