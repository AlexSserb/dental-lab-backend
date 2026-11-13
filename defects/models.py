import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from pgvector.django import HnswIndex, VectorField

from core.models import BaseModel


class DefectType(models.TextChoices):
    FIT = "fit", "Посадка / краевое прилегание"
    COLOR = "color", "Несоответствие цвета"
    POROSITY = "porosity", "Пористость / пузыри"
    CRACK_CHIPPING = "crack_chipping", "Трещины / сколы"
    OTHER = "other", "Другое"


class DefectSeverity(models.TextChoices):
    LOW = "low", "Незначительный"
    MEDIUM = "medium", "Значительный"
    HIGH = "high", "Критический"


class DefectTriage(BaseModel):
    """
    One run of the defect triage workflow: a reported defect, the model's proposal and the administrator's decision.
    The row id doubles as the LangGraph thread id, so a paused graph can be found from the row and vice versa.
    """

    class State(models.TextChoices):
        SUBMITTED = "submitted", "Ожидает обработки"
        PROCESSING = "processing", "Обрабатывается"
        AWAITING_REVIEW = "awaiting_review", "Ожидает решения администратора"
        DECIDED = "decided", "Решение принято, ожидает применения"
        APPLIED = "applied", "Применено"
        REJECTED = "rejected", "Отклонено"
        FAILED = "failed", "Ошибка обработки"

    # A triage in one of these states still needs somebody (the worker or the administrator) to act.
    OPEN_STATES = (State.SUBMITTED, State.PROCESSING, State.AWAITING_REVIEW, State.DECIDED)

    class Decision(models.TextChoices):
        APPROVE = "approve", "Утвердить"
        EDIT = "edit", "Утвердить с правками"
        REJECT = "reject", "Предложить заново"
        DISMISS = "dismiss", "Закрыть без изменений"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="defect_triages", verbose_name="Заказ",
    )
    works = models.ManyToManyField("works.Work", related_name="defect_triages", verbose_name="Работы с дефектом")
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="reported_defect_triages", verbose_name="Сообщил о дефекте",
    )
    comment = models.CharField(max_length=500, blank=True, default="", verbose_name="Комментарий")
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.SUBMITTED, db_index=True, verbose_name="Состояние",
    )

    # What the workflow produced: classification, ids of similar cases, the proposed operation, cause, revisions.
    proposal = models.JSONField(default=dict, blank=True, verbose_name="Предложение")
    # How many times the administrator asked for a new proposal.
    revisions = models.PositiveSmallIntegerField(default=0, verbose_name="Число пересмотров")

    decision = models.CharField(max_length=8, choices=Decision.choices, blank=True, default="", verbose_name="Решение")
    decision_note = models.CharField(max_length=500, blank=True, default="", verbose_name="Комментарий к решению")
    # Values the administrator confirmed or edited; this is what gets applied.
    final = models.JSONField(default=dict, blank=True, verbose_name="Итоговые значения")
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="decided_defect_triages", verbose_name="Решение принял",
    )
    decided_at = models.DateTimeField(null=True, blank=True, verbose_name="Решение принято")
    applied_at = models.DateTimeField(null=True, blank=True, verbose_name="Применено")
    notified_at = models.DateTimeField(null=True, blank=True, verbose_name="Уведомление отправлено")

    error = models.TextField(blank=True, default="", verbose_name="Ошибка")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Разбор дефекта"
        verbose_name_plural = "Разборы дефектов"
        ordering = ["-created_at"]
        constraints = [
            # One unfinished triage per order: a repeated report must not start a second graph for the same defect.
            models.UniqueConstraint(
                fields=["order"],
                condition=Q(state__in=["submitted", "processing", "awaiting_review", "decided"]),
                name="unique_open_defect_triage_per_order",
            ),
        ]

    def __str__(self):
        return f"Разбор дефекта {self.id} ({self.get_state_display()})"

    @property
    def thread_id(self) -> str:
        return str(self.id)


class DefectCase(BaseModel):
    """
    A closed defect used as a precedent for future triages. Holds technical facts only: no customer, doctor or
    order references, so it can be shown to the model and to any administrator.
    """

    class Source(models.TextChoices):
        SEED = "seed", "Демонстрационный"
        TRIAGE = "triage", "Из разбора дефекта"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    triage = models.OneToOneField(
        DefectTriage, null=True, blank=True, on_delete=models.SET_NULL, related_name="case", verbose_name="Разбор",
    )
    source = models.CharField(max_length=8, choices=Source.choices, default=Source.TRIAGE, verbose_name="Источник")
    defect_type = models.CharField(max_length=16, choices=DefectType.choices, verbose_name="Тип дефекта")
    severity = models.CharField(max_length=8, choices=DefectSeverity.choices, verbose_name="Серьёзность")
    operation_type = models.ForeignKey(
        "operations.OperationType", null=True, blank=True, on_delete=models.SET_NULL, related_name="defect_cases",
        verbose_name="Повторенная операция",
    )
    description = models.TextField(verbose_name="Описание дефекта")
    cause = models.TextField(verbose_name="Причина")
    resolution = models.TextField(blank=True, default="", verbose_name="Что было сделано")
    # The text that is embedded and shown to the model as a precedent.
    search_text = models.TextField(verbose_name="Текст для поиска")
    # Must match Chunk.embedding (bge-m3 -> 1024). Null until embedded; HNSW skips null vectors.
    embedding = VectorField(dimensions=1024, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Закрытый случай дефекта"
        verbose_name_plural = "Закрытые случаи дефектов"
        ordering = ["-created_at"]
        indexes = [
            HnswIndex(
                name="defect_case_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self):
        return f"{self.get_defect_type_display()} / {self.get_severity_display()}"
