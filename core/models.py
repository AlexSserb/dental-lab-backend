from django.db import models


class BaseModel(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
