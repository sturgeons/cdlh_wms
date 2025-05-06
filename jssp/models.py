from django.db import models
from django.shortcuts import render

# Create your models here.

class partno(models.Model):
    partno = models.CharField(max_length=20,blank=True,null=True)
    partname = models.CharField(max_length=20,blank=True,null=True)
    parttype = models.CharField(max_length=20,blank=True,null=True)
    partnum = models.CharField(max_length=20,blank=True,null=True)
    partCode = models.CharField(max_length=20,blank=True,null=True)
    partColor = models.CharField(max_length=20,blank=True,null=True)
    # 创建一个ASCII码的partno
    partno_ascii = models.CharField(max_length=2,blank=True,null=True)
    # 车型
    car_type = models.CharField(max_length=20,blank=True,null=True)

# 发运单
class delivery_order(models.Model):
    order_time = models.DateTimeField(blank=True,null=True)
    order_status = models.CharField(max_length=20,blank=True,null=True)
    order_type = models.CharField(max_length=20,blank=True,null=True)
    order_start_id = models.IntegerField(blank=True,null=True)
    order_size = models.IntegerField(blank=True,null=True)

# 发运单明细
class delivery_order_detail(models.Model):
    order_id = models.ForeignKey(delivery_order,on_delete=models.CASCADE)
    lfdnr = models.IntegerField(blank=True,null=True,db_comment='发运单号')
    vin = models.CharField(max_length=20,blank=True,null=True,db_comment='车架号')
    part_color = models.CharField(max_length=20,blank=True,null=True,db_comment='零件颜色')
    car_type = models.CharField(max_length=20,blank=True,null=True,db_comment='适用车型')
    part_ascii = models.CharField(max_length=2,blank=True,null=True,db_comment='零件ASCII码')
    mzeit = models.DateTimeField(max_length=20,blank=True,null=True,db_comment='制造时间')
    position = models.CharField(max_length=20,blank=True,null=True,db_comment='位置')
    knr = models.CharField(max_length=20,blank=True,null=True,db_comment='KNR')
    factory = models.CharField(max_length=20,blank=True,null=True,db_comment='工厂')
    product_line = models.CharField(max_length=20,blank=True,null=True,db_comment='产线')
    order_no = models.CharField(max_length=20,blank=True,null=True,db_comment='订单号')
    left_part_no = models.CharField(max_length=20,blank=True,null=True,db_comment='左侧零件')
    left_part_name = models.CharField(max_length=20,blank=True,null=True,db_comment='左侧零件名称')
    left_part_type = models.CharField(max_length=20,blank=True,null=True,db_comment='左侧零件类型')
    left_part_code = models.CharField(max_length=20,blank=True,null=True,db_comment='左侧零件编码')
    left_part_ascii = models.CharField(max_length=2,blank=True,null=True,db_comment='左侧零件ASCII码')
    left_part_color = models.CharField(max_length=20,blank=True,null=True,db_comment='左侧零件颜色')
    left_part_sn = models.CharField(max_length=20,blank=True,null=True,db_comment='左侧零件SN')
    
    right_part_no = models.CharField(max_length=20,blank=True,null=True,db_comment='右侧零件')
    right_part_name = models.CharField(max_length=20,blank=True,null=True,db_comment='右侧零件名称')
    right_part_type = models.CharField(max_length=20,blank=True,null=True,db_comment='右侧零件类型')
    right_part_code = models.CharField(max_length=20,blank=True,null=True,db_comment='右侧零件编码')
    right_part_ascii = models.CharField(max_length=2,blank=True,null=True,db_comment='右侧零件ASCII码')
    right_part_color = models.CharField(max_length=20,blank=True,null=True,db_comment='右侧零件颜色')
    right_part_sn = models.CharField(max_length=20,blank=True,null=True,db_comment='右侧零件SN')
    
    
