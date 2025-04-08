from django.core.management import BaseCommand

from orders.models import Order


class Command(BaseCommand):
    def handle(self, **options):
        Order.objects.all().delete()
