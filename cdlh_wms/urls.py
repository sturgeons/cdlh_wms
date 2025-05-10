from django.contrib import admin
from django.urls import path, include
import jssp.views
import jssp.views_export_pdf
import jssp.views_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', jssp.views.get_jss_data, name='get_jss_data'),
    path('test/', jssp.views.get_test_data, name='get_test_data'),
    
    # 零件号管理相关URL
    path('parts/', jssp.views.parts_management, name='parts_management'),
    path('parts/save/', jssp.views.save_part, name='save_part'),
    path('parts/edit/<int:part_id>/', jssp.views.edit_part, name='edit_part'),
    path('parts/delete/<int:part_id>/', jssp.views.delete_part, name='delete_part'),
    path('parts/quick-add/', jssp.views.quick_add_part, name='quick_add_part'),
    
    # PDF导出
    path('parts/export-pdf/', jssp.views.export_parts_pdf, name='export_parts_pdf'),
    path('jss/export-table-pdf/', jssp.views_export_pdf.generate_delivery_order_pdf, name='export_jss_table_pdf'),
    
    # 发运单管理
    path('delivery/', jssp.views.delivery_order_management, name='delivery_order_management'),
    path('delivery/<int:order_id>/', jssp.views.get_delivery_order_detail, name='delivery_order_detail'),
    path('delivery/complete/<int:order_id>/', jssp.views.mark_delivery_complete, name='mark_delivery_complete'),
    path('delivery/delete/<int:order_id>/', jssp.views.delete_delivery_order, name='delete_delivery_order'),
    
    # API接口
    path('api/parts/', jssp.views_api.get_part_list, name='get_part_list'),
    path('api/delivery_orders/', jssp.views_api.get_delivery_order_list, name='get_delivery_order_list'),
]
