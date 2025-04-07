# accounts/views.py
from rest_framework import generics, permissions
from .models import CustomUser
from .serializers import UserSerializer, MyTokenObtainPairSerializer
from .permissions import IsAdmin, IsCourier, IsOperator
from rest_framework.response import Response
from .tasks import send_verification_sms, send_welcome_email
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserCreateAPIView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # ro‘yxatdan o‘tishga ochiq

    def perform_create(self, serializer):
        user = serializer.save(is_active=False)  # majburan aktiv emas
        user.generate_verification_code()
        user.save()

        if user.phone_number:
            send_verification_sms.delay(user.id, user.verification_code)

        if user.email:
            send_welcome_email.delay(user.email)

class UserListAPIView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]  # faqat admin ko‘rishi mumkin

class UserDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]


class VerifyPhoneAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        code = request.data.get('code')

        if not username or not code:
            return Response({"detail":"username va code kerak"}, status=400)

        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return Response({"detail":"User topilmadi"}, status=404)

        if user.is_active:
            return Response({"detail":"User already active"}, status=200)

        # 1) Agar kod muddati tugagan bo‘lsa:
        if user.is_verification_code_expired():
            user.verification_code = None
            user.save()
            return Response({"detail":"Kod muddati tugagan. Yangi kod oling."}, status=400)

        # 2) Agar user xato urinish limitiga yetgan bo‘lsa:
        if user.verification_attempts >= 3:
            return Response({"detail":"Ko‘p marta xato kiritdingiz. Admin bilan bog‘laning."}, status=400)

        # 3) Kodni solishtirish
        if user.verification_code == code:
            user.is_active = True
            user.verification_code = None
            user.save()
            return Response({"detail":"Telefon tasdiqlandi, endi login qilishingiz mumkin!"})
        else:
            # Xato => urinish +1
            user.verification_attempts += 1
            user.save()
            if user.verification_attempts >= 3:
                return Response({"detail": "3 marta xato. Foydalanuvchi bloklandi yoki admin bilan bog‘laning."}, status=400)
            return Response({"detail":"Kod noto'g'ri. Qayta kiriting."}, status=400)
