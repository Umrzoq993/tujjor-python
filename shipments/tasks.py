from celery import shared_task
from .models import Shipment
import datetime
from django.utils import timezone

@shared_task
def archive_old_shipments():
    one_month_ago = timezone.now() - datetime.timedelta(days=30)
    # misol uchun 30 kundan eski 'delivered' bo'lsa arxivga
    old_delivered = Shipment.objects.filter(status='delivered', updated_at__lt=one_month_ago)
    # bu yerda arxivlash jarayonini bajarasiz
    count = old_delivered.count()
    # ...
    return f"{count} shipments archived"
