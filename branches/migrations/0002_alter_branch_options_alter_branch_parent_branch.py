# Generated by Django 5.1.7 on 2025-03-30 17:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('branches', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='branch',
            options={'ordering': ['name'], 'verbose_name': 'Filial', 'verbose_name_plural': 'Filiallar'},
        ),
        migrations.AlterField(
            model_name='branch',
            name='parent_branch',
            field=models.ForeignKey(blank=True, help_text='Agar filial boshqa filialga bo‘ysunsa, tanlang', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sub_branches', to='branches.branch'),
        ),
    ]
