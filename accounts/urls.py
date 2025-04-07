# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (UserCreateAPIView, UserListAPIView,
                    UserDetailAPIView, VerifyPhoneAPIView,
                    MyTokenObtainPairView)

urlpatterns = [
    path('register/', UserCreateAPIView.as_view(), name='register'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-phone/', VerifyPhoneAPIView.as_view(), name='verify_phone'),
    path('users/', UserListAPIView.as_view(), name='user_list'),
    path('users/<int:pk>/', UserDetailAPIView.as_view(), name='user_detail'),
]
