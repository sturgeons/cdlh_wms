from django.shortcuts import render
from .models import partno
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from .models import delivery_order, delivery_order_detail

class partnoSerial(serializers.ModelSerializer):
    class Meta:
        model = partno
        fields = '__all__'

class delivery_orderSerial(serializers.ModelSerializer):
    class Meta:
        model = delivery_order
        fields = '__all__'

class delivery_order_detailSerial(serializers.ModelSerializer):
    class Meta:
        model = delivery_order_detail
        fields = '__all__'

def get_part_list(request):
    """获取零件列表"""
    parts = partno.objects.all()
    serializer = partnoSerial(parts, many=True)
    return JsonResponse(serializer.data, safe=False)

def get_delivery_order_list(request):
    """获取发运单列表"""
    delivery_orders = delivery_order.objects.all()
    serializer = delivery_orderSerial(delivery_orders, many=True)
    return JsonResponse(serializer.data, safe=False)

def get_delivery_order_detail(request, order_id):
    """获取发运单详情"""
    _delivery_order = delivery_order.objects.get(id=order_id)
    # 获取发运单详情
    _delivery_order_detail = delivery_order_detail.objects.filter(order_id=_delivery_order)
    serializer = delivery_order_detailSerial(_delivery_order_detail, many=True)

    
    return JsonResponse(serializer.data, safe=False)

