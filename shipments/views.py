# shipments/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Shipment, ShipmentStatusHistory, ShipmentHistory
from .serializers import ShipmentSerializer, ShipmentStatusHistorySerializer, ShipmentHistorySerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from accounts.models import CustomUser
from .permissions import IsAdminOrOperator, IsAdmin
import logging
logger = logging.getLogger(__name__)
from rest_framework.views import APIView
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.shortcuts import get_object_or_404
import qrcode
from io import BytesIO
import os


def generate_invoice_file(shipment_id):
    shipment = get_object_or_404(Shipment, id=shipment_id)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    # Sarlavha
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "YUK XATI")

    # Ma'lumotlar
    p.setFont("Helvetica", 12)
    p.drawString(50, 770, f"Tracking: {shipment.tracking_code}")
    p.drawString(50, 750, f"Yuboruvchi: {shipment.sender_name} ({shipment.sender_phone})")
    p.drawString(50, 730, f"Qabul qiluvchi: {shipment.receiver_name} ({shipment.receiver_phone})")
    p.drawString(50, 710, f"Og‘irligi: {shipment.weight} kg")
    p.drawString(50, 690, f"To‘lov holati: {shipment.payment_status}")
    p.drawString(50, 670, f"To‘lov narxi: {shipment.delivery_price} so‘m")

    # QR Code
    qr_data = f"Tujjor Express\nTracking: {shipment.tracking_code}"
    qr_img = qrcode.make(qr_data)
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer)
    qr_buffer.seek(0)
    p.drawInlineImage(qr_buffer, 400, 700, 120, 120)

    p.showPage()
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

def notify_status_change(shipment, old_status):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "shipments_group",
        {
            "type": "shipment_status_changed",
            "shipment_id": shipment.id,
            "old_status": old_status,
            "new_status": shipment.status,
            "tracking_code": shipment.tracking_code,
        },
    )

class ShipmentViewSet(viewsets.ModelViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'sender', 'receiver_name']
    search_fields = ['receiver_name', 'receiver_phone']

    def perform_create(self, serializer):
        user = self.request.user
        # 1) Yaratgan odamni sender qilamiz
        # 2) Agar user roli 'operator' bo‘lsa, status = 'approved'
        #    Aks holda, 'client_created'
        if user.role in ['admin','operator']:
            # operator/admin to‘g‘ridan-to‘g‘ri tasdiqlangan
            shipment = serializer.save(sender=user, status='approved')
            self._log_history(shipment, f"Shipment created by operator: {user.username}")
        else:
            # mijoz bo‘lsa
            shipment = serializer.save(sender=user, status='client_created')
            self._log_history(shipment, f"Shipment created by client: {user.username}")

    def _log_history(self, shipment, text):
        ShipmentHistory.objects.create(
            shipment=shipment,
            log_text=text
        )

    @action(detail=True, methods=["get"], url_path="invoice", permission_classes=[AllowAny])
    def invoice(self, request, pk=None):
        return generate_invoice_file(pk)

    # operator yoki admin tasdiqlash uchun action
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        # operator yoki admin bo‘lsin
        if request.user.role not in ['admin', 'operator']:
            return Response({"detail": "Ruxsat yo‘q"}, status=403)

        shipment = self.get_object()
        if shipment.status != 'client_created':
            return Response({"detail": "Bu yuk client_created holatida emas"}, status=400)

        old_status = shipment.status
        shipment.status = 'approved'
        shipment.save()

        self._log_history(shipment, f"Operator {request.user.username} approved the shipment (was {old_status})")

        return Response({"detail": "Shipment approved"})

    @action(detail=True, methods=['post'])
    def assign_courier(self, request, pk=None):
        shipment = self.get_object()
        old_courier = shipment.assigned_courier
        old_courier_name = old_courier.username if old_courier else "None"
        old_courier_role = old_courier.role if old_courier else "None"

        courier_id = request.data.get('courier_id')
        new_courier = CustomUser.objects.get(id=courier_id)

        shipment.assigned_courier = new_courier
        shipment.save()

        log_text = (
            f"Courier changed from {old_courier_name} (role: {old_courier_role}) "
            f"to {new_courier.username} (role: {new_courier.role}). "
            f"Status is now {shipment.status}. Branch: {shipment.origin_branch.name} -> {shipment.destination_branch.name}"
        )
        ShipmentHistory.objects.create(shipment=shipment, log_text=log_text)

        return Response({"detail": f"Shipment assigned to {new_courier.username}"})

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        shipment = self.get_object()
        old_status = shipment.status
        new_status = request.data.get('status')

        # Avval eski holatni textda yozib olaylik
        courier_name = shipment.assigned_courier.username if shipment.assigned_courier else "None"
        courier_role = shipment.assigned_courier.role if shipment.assigned_courier else "None"

        shipment.status = new_status
        shipment.save()

        # 🔔 NOTIFICATION
        notify_status_change(shipment, old_status)

        log_text = (
            f"Old Status: {old_status} -> New Status: {new_status}. "
            f"Courier: {courier_name} (role: {courier_role}). "
            f"Origin Branch: {shipment.origin_branch.name if shipment.origin_branch else 'None'} "
            f"Dest Branch: {shipment.destination_branch.name if shipment.destination_branch else 'None'}"
        )
        ShipmentHistory.objects.create(
            shipment=shipment,
            log_text=log_text
        )

        return Response({"detail": f"Status changed from {old_status} to {new_status}"})


class ShipmentTrackView(APIView):
    # Bu endpoint har kimga ochiq bo‘lishi mumkin
    permission_classes = []

    def get(self, request, code):
        # 1) tracking_code orqali shipmentni topish
        try:
            shipment = Shipment.objects.get(tracking_code=code)
        except Shipment.DoesNotExist:
            return Response({"detail":"Bunday tracking code topilmadi"}, status=404)

        # 2) history ro‘yxatini vaqt tartibida olish
        histories = shipment.history.order_by('created_at')

        # 3) Yakuniy text format
        # namuna:
        # 1. Namangan viloyati Namangan shahri: 2024-11-29 01:29:13 : Turgunov Durbek
        # ...
        # 🔄 Yuk holati: 🟢 Pochta yetkazib berildi
        # O'zingiz xohlagan formatda jamlashingiz mumkin

        step_list = []
        step_number = 1
        for h in histories:
            line = f"{step_number}. {h.log_text} ({h.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
            step_list.append(line)
            step_number += 1

        final_status = shipment.status
        # Agar final_status == 'delivered', "🟢 Pochta yetkazib berildi" deymiz,
        # bosqichlarga mos emoji yasalishi mumkin
        status_emoji = "🟢 Pochta yetkazib berildi" if final_status=='delivered' else f"Holat: {final_status}"

        # Yig'ish
        response_text = f"🗺 Yuk yo'li tarixi:\n🆔 Yuk raqami: {shipment.tracking_code}\n\n"
        for step_line in step_list:
            response_text += step_line + "\n"

        response_text += f"🔄 Yuk holati: {status_emoji}"

        return Response({"detail": response_text})


class ShipmentStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShipmentStatusHistory.objects.all()
    serializer_class = ShipmentStatusHistorySerializer
    permission_classes = [IsAuthenticated]


class StatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        # 1) bugun yaratilgan yuklar soni
        from django.utils import timezone
        from django.db.models import Count
        today = timezone.now().date()

        # Qancha shipment created_at >= bugun 00:00
        from django.db.models.functions import TruncDate
        shipments_today_count = Shipment.objects.filter(created_at__date=today).count()

        # Filial bo‘yicha grouping
        branch_stats = Shipment.objects.values('origin_branch').annotate(total=Count('id'))

        return Response({
            "shipments_today": shipments_today_count,
            "branch_stats": list(branch_stats),
        })


class ShipmentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShipmentHistory.objects.all()
    serializer_class = ShipmentHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['shipment']