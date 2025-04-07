from django.contrib import admin
from django.urls import path, include
from shipments.urls import router as shipments_router
from branches.urls import router as branches_router
from payments.urls import router as payments_router
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # JWT
    # accounts
    path('api/accounts/', include('accounts.urls')),
    # shipments
    path('api/shipments/', include(shipments_router.urls)),
    # branches
    path('api/branches/', include(branches_router.urls)),
    # payments
    path('api/payments/', include(payments_router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
