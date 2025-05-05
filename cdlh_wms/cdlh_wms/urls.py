from django.contrib import admin
from django.urls import path, include
import jssp.views
import jssp.views_export_pdf

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
    path('jss/export-table-pdf/', jssp.views_export_pdf.export_jss_table_pdf, name='export_jss_table_pdf'),
]
