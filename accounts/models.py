from django.db import models
from django.contrib.auth.models import AbstractUser
import secrets
from django.utils import timezone
import datetime
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('operator', 'Operator'),
        ('courier', 'Kuryer'),
        ('physical', 'Jismoniy Shaxs'),
        ('legal', 'Yuridik Shaxs'),
    )

    # 1) is_active ni default=False
    is_active = models.BooleanField(default=False)

    # 2) verification_code
    verification_code = models.CharField(max_length=6, blank=True, null=True)

    # Kod yaratilgan vaqt, xohlasak 5 daqiqa ichida amal qiladi
    verification_code_created = models.DateTimeField(blank=True, null=True)

    # Necha marta xato kirgan
    verification_attempts = models.PositiveSmallIntegerField(default=0)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='physical', help_text="Foydalanuvchi roli")
    company_name = models.CharField(max_length=255, blank=True, null=True, help_text="Agar yuridik shaxs bo‘lsa, kompaniya nomi")
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Foydalanuvchi telefon raqami")

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-date_joined']

    def generate_verification_code(self):
        code = str(secrets.randbelow(10**6)).zfill(6)
        self.verification_code = code
        self.verification_code_created = timezone.now()
        self.verification_attempts = 0

    def is_verification_code_expired(self):
        """5 daqiqa"""
        if not self.verification_code_created:
            return True
        delta = timezone.now() - self.verification_code_created
        return delta > datetime.timedelta(minutes=5)

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
