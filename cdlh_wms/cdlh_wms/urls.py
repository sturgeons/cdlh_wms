
from django.contrib import admin
from django.urls import path, include
import jssp.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', jssp.views.get_jss_data, name='get_jss_data'),
]
