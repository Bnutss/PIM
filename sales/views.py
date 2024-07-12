from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import LoginSerializer
from rest_framework.response import Response
from rest_framework import generics
from .models import Materials, Coming, Stock, Expenses, StockMaterials
from .serializers import MaterialsSerializer, ComingSerializer, StockSerializer, ExpensesSerializer, \
    StockMaterialsSerializer
from rest_framework import status
from rest_framework.decorators import api_view
from datetime import timedelta, datetime
from django.utils import timezone
from .telegram_utils import send_telegram_message


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            return Response({"message": "Успешный вход!", "user_id": user.id})
        return Response(serializer.errors, status=400)


class MaterialsListAPIView(generics.ListAPIView):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer

    def get_queryset(self):
        return Materials.objects.all()


class AddMaterialsAPIView(APIView):

    def post(self, request, *args, **kwargs):
        serializer = MaterialsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MaterialsDeleteView(generics.DestroyAPIView):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ComingCreateAPIView(generics.CreateAPIView):
    queryset = Coming.objects.all()
    serializer_class = ComingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ExpensesCreateAPIView(generics.CreateAPIView):
    queryset = Expenses.objects.all()
    serializer_class = ExpensesSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        stock_id = data.get('stock')
        material_id = data.get('material')
        quantity = float(data.get('quantity'))

        try:
            stock_material = StockMaterials.objects.get(stock_id=stock_id, material_id=material_id)
            if stock_material.quantity < quantity:
                return Response(
                    {"error": "Недостаточно материала на складе"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except StockMaterials.DoesNotExist:
            return Response(
                {"error": "Материал на складе не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@api_view(['GET'])
def materials_by_stock(request, stock_id):
    try:
        stock_materials = StockMaterials.objects.filter(stock_id=stock_id, quantity__gt=0)
        materials = [sm.material for sm in stock_materials]
        serializer = MaterialsSerializer(materials, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except StockMaterials.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def stock_material_quantity(request, stock_id, material_id):
    try:
        stock_material = StockMaterials.objects.get(stock_id=stock_id, material_id=material_id)
        return Response({'quantity': stock_material.quantity}, status=status.HTTP_200_OK)
    except StockMaterials.DoesNotExist:
        return Response(
            {"error": "Материал на складе не найден"},
            status=status.HTTP_404_NOT_FOUND
        )


class StockListAPIView(generics.ListAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer

    def get_queryset(self):
        return Stock.objects.all()


class DailySummaryView(APIView):
    def get(self, request, format=None):
        date_str = request.query_params.get('date', None)
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()

        start_of_day = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end_of_day = start_of_day + timedelta(days=1)

        filter_type = request.query_params.get('filter', 'all')

        comings = Coming.objects.filter(arrival_date__range=(start_of_day, end_of_day))
        expenses = Expenses.objects.filter(expenses_date__range=(start_of_day, end_of_day))

        if filter_type == 'comings':
            expenses = []
        elif filter_type == 'expenses':
            comings = []
        elif filter_type == 'credit':
            comings = []
            expenses = expenses.filter(on_credit=True)

        total_comings = sum(coming.quantity * coming.price for coming in comings)
        total_expenses = sum(expense.quantity * expense.price for expense in expenses)
        total_credit = sum(expense.quantity * expense.price for expense in expenses if expense.on_credit)

        data = {
            'comings': ComingSerializer(comings, many=True).data,
            'expenses': ExpensesSerializer(expenses, many=True).data,
            'total_comings': total_comings,
            'total_expenses': total_expenses,
            'total_credit': total_credit,
        }

        if filter_type == 'comings':
            data = {'total_comings': total_comings, 'comings': data['comings']}
        elif filter_type == 'expenses':
            data = {'total_expenses': total_expenses, 'expenses': data['expenses']}
        elif filter_type == 'credit':
            data = {'total_credit': total_credit, 'expenses': data['expenses']}

        return Response(data)


class SendToTelegramView(APIView):
    def post(self, request, format=None):
        date_str = request.query_params.get('date', None)
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()

        filter_type = request.query_params.get('type', 'all')

        start_of_day = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end_of_day = start_of_day + timedelta(days=1)

        comings = Coming.objects.filter(arrival_date__range=(start_of_day, end_of_day))
        expenses = Expenses.objects.filter(expenses_date__range=(start_of_day, end_of_day))

        if filter_type == 'comings':
            expenses = []
        elif filter_type == 'expenses':
            comings = []
        elif filter_type == 'credit':
            comings = []
            expenses = expenses.filter(on_credit=True)

        total_comings = sum(coming.quantity * coming.price for coming in comings)
        total_expenses = sum(expense.quantity * expense.price for expense in expenses)
        total_credit = sum(expense.quantity * expense.price for expense in expenses if expense.on_credit)

        def format_number(number):
            return f"{number:,.0f}".replace(',', ' ')

        date_str = date.strftime('%d-%m-%Y')
        message_header = f"Дата: {date_str}\n\n"

        if filter_type == 'comings':
            message = message_header + f"Итог прихода: {format_number(total_comings)} UZS\n\n" + "\n".join(
                [
                    f"{coming.material.name}: {coming.quantity} {coming.material.unit} x {format_number(coming.price)} UZS\n"
                    for coming in comings])
        elif filter_type == 'expenses':
            message = message_header + f"Итог расхода: {format_number(total_expenses)} UZS\n" + "\n".join(
                [
                    f"{expense.material.name}: {expense.quantity} {expense.material.unit} x {format_number(expense.price)} UZS"
                    for expense in expenses])
        elif filter_type == 'credit':
            message = message_header + f"Итог долга: {format_number(total_credit)} UZS\n" + "\n".join([
                f"{expense.material.name} (Должник: {expense.debtor_name}): {expense.quantity} {expense.material.unit} x {format_number(expense.price)} UZS"
                for expense in expenses])
        else:
            message = (message_header +
                       f"Итог прихода: {format_number(total_comings)} UZS\n\n" +
                       "\n".join(
                           [
                               f"{coming.material.name}: {coming.quantity} {coming.material.unit} x {format_number(coming.price)} UZS"
                               for coming in comings]) +
                       f"\n\nИтог расхода: {format_number(total_expenses)} UZS\n\n" +
                       "\n".join(
                           [
                               f"{expense.material.name}: {expense.quantity} {expense.material.unit} x {format_number(expense.price)} UZS"
                               for expense in expenses]) +
                       f"\n\nИтог долга: {format_number(total_credit)} UZS\n\n" +
                       "\n".join([
                           f"{expense.material.name} (Должник: {expense.debtor_name}): {expense.quantity} {expense.material.unit} x {format_number(expense.price)} UZS"
                           for expense in expenses if expense.on_credit]))

        send_telegram_message(message)

        return Response({"status": "Сообщение отправлено в Telegram"})


@api_view(['GET', 'POST'])
def stockmaterials_list(request):
    if request.method == 'GET':
        stock_id = request.query_params.get('stock_id')
        if stock_id:
            stockmaterials = StockMaterials.objects.filter(stock_id=stock_id)
        else:
            stockmaterials = StockMaterials.objects.all()
        serializer = StockMaterialsSerializer(stockmaterials, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = StockMaterialsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
