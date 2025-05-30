# branches/urls.py
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet

router = DefaultRouter()
router.register(r'branches', BranchViewSet, basename='branch')

urlpatterns = router.urls
