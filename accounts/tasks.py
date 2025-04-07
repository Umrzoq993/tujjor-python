from .models import CustomUser
from .sms_utils import transmit_sms
import os
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_verification_sms(user_id, code):
    try:
        user = CustomUser.objects.get(id=user_id)
        if user.phone_number:
            sms_id = f"user_{user.id}"
            text = f"Your code: {code}"
            transmit_sms(text, sms_id, user.phone_number)
    except CustomUser.DoesNotExist:
        pass


@shared_task
def send_welcome_email(user_email):
    subject = "Xush kelibsiz!"
    message = "Ro‘yxatdan o‘tgansiz. Endi yuk yetkazish xizmatidan foydalanishingiz mumkin."
    from_email = os.getenv('DEFAULT_FROM_EMAIL','info@example.com')
    send_mail(subject, message, from_email, [user_email])