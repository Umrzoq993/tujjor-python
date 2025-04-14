import re
from django.db import models
from django.conf import settings
from branches.models import Branch
from django.db.models import JSONField

class Shipment(models.Model):
    STATUS_CHOICES = (
        ('client_created', 'Mijoz kiritgan, operator tasdiqini kutmoqda'),
        ('approved', 'Operator tasdiqladi'),
        ('in_transit', 'Yo‘lda'),
        ('arrived', 'Yetib keldi'),
        ('delivered', 'Topshirildi'),
    )
    PICKUP_TYPE = (
        ('office_dropoff', 'Jo‘natuvchi ofisga olib keladi'),
        ('courier_pickup', 'Kuryer chaqirtirish')
    )
    DELIVERY_TYPE = (
        ('office_pickup', 'Qabul qiluvchi ofisdan oladi'),
        ('courier_delivery', 'Kuryer olib boradi')
    )
    PAYMENT_RESPONSIBILITY = (
        ('sender', 'Yuboruvchi to‘laydi'),
        ('receiver', 'Qabul qiluvchi to‘laydi')
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_shipments',
        help_text="Trek raqam, UUID ko'rinishida"
    )
    origin_branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shipments_from'
    )
    destination_branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shipments_to'
    )

    receiver_name = models.CharField(max_length=255)
    receiver_phone = models.CharField(max_length=50, blank=True, null=True)
    weight = models.FloatField(help_text="Og‘irlik (kg)")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # yangi statuslar:
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='client_created')

    # T + 9 xonali kod, unik bo‘ladi
    tracking_code = models.CharField(max_length=10, unique=True, blank=True, null=True)

    # 1) Jo‘natish qanday bo‘ladi?
    pickup_type = models.CharField(max_length=20, choices=PICKUP_TYPE, default='office_dropoff')
    # 2) Yetkazish qanday bo‘ladi?
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPE, default='office_pickup')
    # 3) To‘lovni kim qiladi?
    payment_responsibility = models.CharField(max_length=20, choices=PAYMENT_RESPONSIBILITY, default='sender')

    assigned_courier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_shipments',
        limit_choices_to={'role': 'courier'},
        help_text="Bu yukni kuryerga biriktirish uchun"
    )

    class Meta:
        verbose_name = 'Yuk'
        verbose_name_plural = 'Yuklar'
        ordering = ['-created_at']

    def __str__(self):
        return f"Shipment #{self.id} ({self.tracking_code}) - {self.sender} ➜ {self.receiver_name}"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        old_status = None

        if not creating:
            old_status = Shipment.objects.get(pk=self.pk).status

        # 1) tracking_code bo'sh bo‘lsa, avtomatik generatsiya
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()

        # 2) Narxni avto-hisoblash
        if not self.price:
            self.price = self.calculate_price()

        super().save(*args, **kwargs)

        if old_status and old_status != self.status:
            ShipmentStatusHistory.objects.create(
                shipment=self,
                old_status=old_status,
                new_status=self.status
            )

    def generate_tracking_code(self):
        """Oxirgi shipmentni topib, tracking_code ni increment qilamiz"""
        last_shipment = Shipment.objects.order_by('-id').first()
        if not last_shipment or not last_shipment.tracking_code:
            new_number = 1
        else:
            # T000219457 dan 219457 ni olish:
            match = re.match(r'^T(\d{9})$', last_shipment.tracking_code)
            if match:
                last_num = int(match.group(1))  # 219457
                new_number = last_num + 1
            else:
                # agar patternni topa olmasa, 1 dan boshlaymiz
                new_number = 1

        # Masalan T000000001 shaklida formatlash
        return f"T{new_number:09d}"


    def calculate_price(self):
        """Og‘irlikka asosiy narx + kuryer xizmati bo‘lsa qo‘shimcha qo‘shish."""
        base_rate = 10000  # 1 kg = 10000 so‘m, misol
        amount = self.weight * base_rate

        # Agar kuryer chaqirtirilsa (pickup_type='courier_pickup'), masalan, +15000 so‘m
        if self.pickup_type == 'courier_pickup':
            amount += 15000

        # Agar yetkazish ham kuryer orqali bo‘lsa (delivery_type='courier_delivery'), +15000 so‘m
        if self.delivery_type == 'courier_delivery':
            amount += 15000

class ShipmentStatusHistory(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Yuk holati tarixi'
        verbose_name_plural = 'Yuk holati tarixi'
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.shipment} | {self.old_status} ➜ {self.new_status}"


class ShipmentHistory(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='history')
    created_at = models.DateTimeField(auto_now_add=True)
    log_text = models.TextField(help_text="Yuk tarixi haqida ma'lumot", blank=True, null=True)
    ordering = ['-created_at']

    def __str__(self):
        return f"[{self.created_at}] Shipment {self.shipment.tracking_code}: {self.log_text}"