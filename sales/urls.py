from django.urls import path
from .views import LoginAPIView, MaterialsListAPIView, AddMaterialsAPIView, MaterialsDeleteView, ComingCreateAPIView, \
    StockListAPIView, ExpensesCreateAPIView, materials_by_stock, stock_material_quantity, DailySummaryView, \
    SendToTelegramView, stockmaterials_list

app_name = 'sales'

urlpatterns = [
    path('api/login/', LoginAPIView.as_view(), name='api_login'),
    path('api/materials/', MaterialsListAPIView.as_view(), name='materials-list-api'),
    path('api/add-materials/', AddMaterialsAPIView.as_view(), name='add_materials_api'),
    path('api/materials/<int:pk>/delete/', MaterialsDeleteView.as_view(), name='materials-delete_api'),
    path('api/coming/', ComingCreateAPIView.as_view(), name='coming-create_api'),
    path('api/expenses/', ExpensesCreateAPIView.as_view(), name='expenses-create_api'),
    path('api/materials/by_stock/<int:stock_id>/', materials_by_stock, name='materials-by-stock'),
    path('api/stock_materials/<int:stock_id>/<int:material_id>/', stock_material_quantity,
         name='stock-material-quantity'),
    path('api/stock/', StockListAPIView.as_view(), name='stock-list-api'),
    path('api/daily-summary/', DailySummaryView.as_view(), name='daily-summary'),
    path('api/send-telegram/', SendToTelegramView.as_view(), name='send-telegram'),
    path('api/stockmaterials/', stockmaterials_list, name='stockmaterials_list'),
]
