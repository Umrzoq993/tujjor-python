# Generated by Django 5.1.7 on 2025-03-30 08:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receiver_name', models.CharField(max_length=255)),
                ('receiver_phone', models.CharField(blank=True, max_length=50, null=True)),
                ('weight', models.FloatField(help_text='Og‘irlik (kg)')),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('status', models.CharField(choices=[('created', 'Yaratilgan'), ('accepted', 'Qabul qilindi'), ('in_transit', 'Yo‘lda'), ('arrived', 'Yetib keldi'), ('delivered', 'Topshirildi')], default='created', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_shipments', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ShipmentStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_status', models.CharField(max_length=20)),
                ('new_status', models.CharField(max_length=20)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('shipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='shipments.shipment')),
            ],
        ),
    ]
