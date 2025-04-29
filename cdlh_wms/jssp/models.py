from django.db import models
from django.shortcuts import render

# Create your models here.

def get_jss_data(request):


    return render(request, 'jssp/index.html')

