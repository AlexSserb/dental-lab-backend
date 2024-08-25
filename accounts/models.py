
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import (
    MinLengthValidator,
    MaxValueValidator,
)
from django.db import models

from accounts.singleton import SingletonModel


class CustomUserManager(BaseUserManager):
    def create_user(cls, self, email, password, **other_fields):
        email = BaseUserManager.normalize_email(email)
        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, email, password, **other_fields):
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_superuser", True)
        other_fields.setdefault("is_active", True)

        return self.create_user(self, email, password, **other_fields)


# Customer (Clinic/Hospital)
class Customer(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    name = models.CharField(
        max_length=256,
        verbose_name="Наименование организации",
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="Номер телефона",
    )
    # ИНН
    tax_payer_id = models.CharField(
        max_length=12,
        validators=[MinLengthValidator(12)],
        unique=True,
        verbose_name="ИНН",
    )
    # КПП
    reason_code_for_reg = models.CharField(
        max_length=9,
        validators=[MinLengthValidator(9)],
        unique=True,
        verbose_name="КПП",
    )
    # Р/с
    checking_account = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(20)],
        unique=True,
        verbose_name="Р/с",
    )
    adrs_city = models.CharField(max_length=64, verbose_name="Город")
    adrs_street = models.CharField(max_length=64, verbose_name="Улица")
    adrs_house = models.PositiveIntegerField(validators=[MaxValueValidator(10000)], verbose_name="Дом")
    mail_index = models.CharField(max_length=6, validators=[MinLengthValidator(6)], verbose_name="Почтовый индекс")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Заказчик"
        verbose_name_plural = "Заказчики"

    def __str__(self):
        return f"{self.name} - г. {self.adrs_city}, ул. {self.adrs_street}, д. {self.adrs_house}"


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, verbose_name="Имя")
    last_name = models.CharField(max_length=30, verbose_name="Фамилия")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    is_staff = models.BooleanField(default=True, verbose_name="Доступ ко входу в админ-панель")
    is_superuser = models.BooleanField(default=False, verbose_name="Доступ к данным админ-панели")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    # Linked clinics and hospitals
    customers = models.ManyToManyField(Customer, verbose_name="Заказчики", blank=True)

    USERNAME_FIELD = "email"
    objects = CustomUserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.email}"


# Данные зуботехнической лаборатории
class DentalLabData(SingletonModel):
    name = models.CharField(max_length=256, verbose_name="Наименование лаборатории")
    # БИК
    bank_id_code = models.CharField(max_length=9, validators=[MinLengthValidator(9)], verbose_name="БИК")
    # Наименование банка
    bank_name = models.CharField(max_length=256, verbose_name="Наименование банка")
    # Номер расчетного счета
    current_account = models.CharField(
        max_length=20, validators=[MinLengthValidator(20)], verbose_name="Расчетный счет"
    )
    # Номер корреспондентского счета
    correspondent_account = models.CharField(
        max_length=20, validators=[MinLengthValidator(20)], verbose_name="Корреспондентский счет"
    )
    # ИНН
    tax_payer_id = models.CharField(
        max_length=12,
        validators=[MinLengthValidator(12)],
        verbose_name="ИНН",
    )
    # КПП
    reason_code_for_reg = models.CharField(
        max_length=9,
        validators=[MinLengthValidator(9)],
        verbose_name="КПП",
    )

    class Meta:
        verbose_name = "Данные лаборатории"
        verbose_name_plural = "Данные лаборатории"
