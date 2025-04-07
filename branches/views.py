# branches/views.py
from rest_framework import viewsets, permissions
from .models import Branch
from .serializers import BranchSerializer

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]
    # misol: create/update/delete faqat admin bo‘lsin
    # read (GET) operator ham qila olishi uchun custom permission qilishingiz mumkin
