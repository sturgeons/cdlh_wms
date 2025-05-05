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

