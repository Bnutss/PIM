from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import Materials, Coming, Stock, Expenses, StockMaterials


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user and user.is_active:
            if hasattr(user, 'userprofile') and user.userprofile.mobile_app:
                return user
            else:
                raise serializers.ValidationError("Этот пользователь не имеет доступа через мобильное приложение.")
        raise serializers.ValidationError("Неправильный логин или пароль.")


class MaterialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materials
        fields = ['id', 'name', 'unit', 'time_create']


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['id', 'name_stock', 'time_create']


class ComingSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_unit = serializers.CharField(source='material.unit', read_only=True)

    class Meta:
        model = Coming
        fields = ['stock', 'material', 'material_name', 'material_unit', 'quantity', 'price', 'arrival_date']

    def create(self, validated_data):
        return Coming.objects.create(**validated_data)


class ExpensesSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_unit = serializers.CharField(source='material.unit', read_only=True)

    class Meta:
        model = Expenses
        fields = ['stock', 'material', 'material_name', 'material_unit', 'quantity', 'price', 'on_credit',
                  'debtor_name', 'expenses_date']


class StockMaterialSerializer(serializers.ModelSerializer):
    stock = StockSerializer()
    material = MaterialsSerializer()

    class Meta:
        model = StockMaterials
        fields = '__all__'


class StockMaterialsSerializer(serializers.ModelSerializer):
    stock_name = serializers.CharField(source='stock.name_stock', read_only=True)
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_unit = serializers.CharField(source='material.unit', read_only=True)

    class Meta:
        model = StockMaterials
        fields = ['id', 'stock_name', 'material_name', 'material_unit', 'quantity', 'avg_price']
