from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    parent_branch = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sub_branches',
        help_text="Agar filial boshqa filialga bo‘ysunsa, tanlang"
    )

    class Meta:
        verbose_name = 'Filial'
        verbose_name_plural = 'Filiallar'
        ordering = ['name']

    def __str__(self):
        return self.name

