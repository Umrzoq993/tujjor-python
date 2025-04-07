# shipments/serializers.py
from rest_framework import serializers
from .models import Shipment, ShipmentStatusHistory

class ShipmentSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    sender_phone = serializers.CharField(source='sender.phone_number', read_only=True)
    sender_first_name = serializers.CharField(source="sender.first_name", read_only=True)
    sender_last_name = serializers.CharField(source="sender.last_name", read_only=True)
    sender_company = serializers.CharField(source='sender.company_name', read_only=True)
    origin_branch_name = serializers.CharField(source='origin_branch.name', read_only=True)
    destination_branch_name = serializers.CharField(source='destination_branch.name', read_only=True)

    class Meta:
        model = Shipment

        fields = [
            'id', 'tracking_code', 'sender', 'sender_name', 'sender_phone', 'sender_first_name',
            'sender_last_name', 'sender_company', 'origin_branch', 'origin_branch_name',
            'destination_branch', 'destination_branch_name', 'receiver_name',
            'receiver_phone', 'weight', 'price', 'status', 'created_at',
            'updated_at', 'pickup_type', 'delivery_type',
            'payment_responsibility', 'assigned_courier'
        ]

        read_only_fields = ['sender', 'price', 'status', 'created_at', 'updated_at']


class ShipmentStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentStatusHistory
        fields = '__all__'
