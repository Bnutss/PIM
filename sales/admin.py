from django.contrib import admin
from sales.models import Stock, Materials, Coming, Expenses, StockMaterials
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


class StockMaterialsAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).exclude(quantity=0)

    list_display = ('stock', 'material', 'quantity', 'avg_price')
    list_display_links = ('stock',)
    search_fields = ('stock', 'material')
    autocomplete_fields = ['stock', 'material']
    list_filter = ('stock', 'material')


class StockAdmin(admin.ModelAdmin):
    list_display = ('name_stock', 'get_users_names')
    list_display_links = ('name_stock',)
    search_fields = ('name_stock',)
    autocomplete_fields = ['users', ]

    def get_users_names(self, obj):
        return ", ".join([user.username for user in obj.users.all()])

    get_users_names.short_description = 'Пользователи'


class MaterialsAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'remainder')
    list_display_links = ('name',)
    search_fields = ('name',)


class ComingAdmin(admin.ModelAdmin):
    list_display = ('material', 'stock', 'quantity', 'is_completed', 'time_create')
    list_display_links = ('material',)
    search_fields = ('material',)
    list_filter = ('stock',)
    autocomplete_fields = ['stock', 'material']


class ExpensesAdmin(admin.ModelAdmin):
    list_display = ('material', 'stock', 'quantity', 'on_credit', 'debtor_name', 'time_create')
    list_display_links = ('material',)
    search_fields = ('material',)
    list_filter = ('stock',)
    autocomplete_fields = ['stock', 'material']


admin.site.register(Stock, StockAdmin)
admin.site.register(Materials, MaterialsAdmin)
admin.site.register(Coming, ComingAdmin)
admin.site.register(Expenses, ExpensesAdmin)
admin.site.register(StockMaterials, StockMaterialsAdmin)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
