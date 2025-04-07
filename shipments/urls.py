from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ShipmentViewSet, ShipmentStatusHistoryViewSet, StatsView,ShipmentTrackView

router = DefaultRouter()
router.register(r'shipments', ShipmentViewSet, basename='shipment')
router.register(r'shipment-status-history', ShipmentStatusHistoryViewSet, basename='shipmentstatushistory')

urlpatterns = router.urls + [
    path('stats/', StatsView.as_view(), name='stats_view'),
    path('shipments/track/<str:code>/', ShipmentTrackView.as_view(), name='shipment_track')
]
