from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    mobile_app = models.BooleanField(default=False, verbose_name='Мобильное приложение')

    def __str__(self):
        return self.user.username


class Stock(models.Model):
    name_stock = models.CharField(max_length=200, verbose_name='Название склада', unique=True)
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время изменения')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    users = models.ManyToManyField(User, blank=True, verbose_name='Пользователи')

    def __str__(self):
        return self.name_stock

    class Meta:
        verbose_name = 'Склад'
        verbose_name_plural = 'Склады'
        ordering = ['-time_create', 'name_stock']


class Materials(models.Model):
    UNIT_CHOICES = (
        ('кг', 'кг'),
        ('шт', 'шт'),
        ('мт', 'мт'),
    )
    name = models.CharField(max_length=100, verbose_name='Наименование')
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES, verbose_name='Единицы измерения')
    remainder = models.FloatField(default=0, verbose_name='Остаток', editable=False)
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время изменения')

    def __str__(self):
        return f'{self.name} {self.unit}'

    class Meta:
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'
        ordering = ['-time_create']


class StockMaterials(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, verbose_name='Склад')
    material = models.ForeignKey(Materials, on_delete=models.CASCADE, verbose_name='Материал')
    quantity = models.FloatField(default=0, verbose_name='Количество', editable=False)
    avg_price = models.FloatField(default=0, verbose_name='Средняя цена', editable=False)

    def __str__(self):
        return f'{self.stock.name_stock} - {self.material.name} ({self.quantity})'

    class Meta:
        verbose_name = 'Материал на складе'
        verbose_name_plural = 'Материалы на складах'


class Coming(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, verbose_name='Склад')
    material = models.ForeignKey(Materials, on_delete=models.CASCADE, verbose_name='Материал')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    is_completed = models.BooleanField(default=False, verbose_name='Оприходовано')
    arrival_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата прихода')

    def __str__(self):
        return f"Приход {self.id} - {self.material}"

    def save(self, *args, **kwargs):
        if not self.arrival_date:
            self.arrival_date = timezone.now()
        self.is_completed = True

        if self._state.adding:
            stock_material, created = StockMaterials.objects.get_or_create(stock=self.stock, material=self.material)
            stock_material.quantity += float(self.quantity)
            if created:
                stock_material.avg_price = float(self.price)
            else:
                stock_material.avg_price = (stock_material.avg_price * stock_material.quantity + float(
                    self.price) * float(self.quantity)) / (stock_material.quantity + float(self.quantity))
            stock_material.save()
            self.material.remainder += float(self.quantity)
            self.material.save()

        super(Coming, self).save(*args, **kwargs)

    def total_cost(self):
        return self.quantity * self.price

    class Meta:
        verbose_name = 'Приход'
        verbose_name_plural = 'Приходы'
        ordering = ['-time_create']


class Expenses(models.Model):
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE, verbose_name='Склад')
    material = models.ForeignKey('Materials', on_delete=models.CASCADE, verbose_name='Материал')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    on_credit = models.BooleanField(default=False, verbose_name='Долг')
    debtor_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Имя должника')
    expenses_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата расхода')

    def __str__(self):
        return f"Расход {self.id} - {self.material}"

    def save(self, *args, **kwargs):
        if not self.expenses_date:
            self.expenses_date = timezone.now()

        if self._state.adding:
            stock_material, created = StockMaterials.objects.get_or_create(stock=self.stock, material=self.material)
            stock_material.quantity -= float(self.quantity)
            stock_material.save()
            self.material.remainder -= float(self.quantity)
            self.material.save()
        super(Expenses, self).save(*args, **kwargs)

    def total_cost(self):
        return self.quantity * self.price

    class Meta:
        verbose_name = 'Расход'
        verbose_name_plural = 'Расходы'
        ordering = ['-time_create']
