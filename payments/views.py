# payments/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Payment
from .serializers import PaymentSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """Soddalashtirilgan: Payment status -> 'paid'."""
        payment = self.get_object()
        payment.status = 'paid'
        payment.save()
        return Response({"detail": "Payment successful"})
