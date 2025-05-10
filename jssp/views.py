from django.shortcuts import render, redirect, get_object_or_404
import requests
from django.http import JsonResponse, HttpResponse
import json
import os
from django.conf import settings
from .models import partno, delivery_order, delivery_order_detail
import tempfile
import platform
from io import BytesIO
from datetime import datetime, timedelta
from django.urls import reverse

# 导入PDF相关库
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Image as RLImage

# 导入二维码库
import qrcode
from PIL import Image

# 从utils模块导入中文字体注册函数
from .utils import register_chinese_font

# Create your views here.


def get_all_data(records_all, current_page):
    url = "http://mgn.delink.top:8005/client/get-client-list"
    headers = {"Content-Type": "application/json"}
    post_data = {
        "pageNum": current_page,
        "accessKey": "5AD",
        "pageSize": 1000,
        "pointStatus": "M100",
        "productLine": "",
    }
    try:
        response = requests.post(url, json=post_data, headers=headers)
        data = response.json()
        records = data.get("records", [])
        total = data.get("total", 0)
        current = data.get("current", 1)
        pages = data.get("pages", 1)

        records_all.extend(records)

        if pages > current_page:
            return get_all_data(records_all, current_page + 1)

        return {
            "records": records_all,
            "total": total,
            "current": current,
            "pages": pages,
        }
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return {"records": records_all, "total": 0, "current": current_page, "pages": 1}


def filter_records_by_start_id(filtered_records, start_id, data):
    """根据起始ID筛选记录

    Args:
        filtered_records: 要筛选的记录列表
        start_id: 起始ID
        data: 数据字典,用于存储错误信息

    Returns:
        筛选后的记录列表
    """
    if not start_id:
        return filtered_records

    try:
        # 将起始ID转换为整数进行比较
        start_id_int = int(start_id)
        # 找到起始ID的索引
        start_index = None
        for i, record in enumerate(filtered_records):
            # 将记录中的lfdnr也转换为整数进行比较
            record_id = int(record.get("lfdnr", 0))
            if record_id >= start_id_int:
                start_index = i
                break

        # 只有找到匹配的记录时才筛选，否则保持原数据
        if start_index is not None:
            filtered_records = filtered_records[start_index:]
        # 如果没找到匹配的记录，添加提示信息
        else:
            data["filter_error"] = (
                f"未找到ID大于等于 {start_id_int} 的记录，显示全部数据"
            )
    except (ValueError, TypeError):
        # 如果转换失败，则使用原始的字符串比较方法
        start_index = None
        for i, record in enumerate(filtered_records):
            if str(record.get("lfdnr")) == start_id:
                start_index = i
                break

        # 只有找到匹配的记录时才筛选，否则保持原数据
        if start_index is not None:
            filtered_records = filtered_records[start_index:]
        # 如果没找到匹配的记录，添加提示信息
        else:
            data["filter_error"] = f"未找到ID为 {start_id} 的记录，显示全部数据"

    return filtered_records


def limit_records_count(filtered_records, limit_count, data_records):
    """限制记录数量

    Args:
        filtered_records: 要限制的记录列表
        limit_count: 限制数量
        data_records: 原始记录列表,用于补充数据

    Returns:
        限制后的记录列表
    """
    if not limit_count or not limit_count.isdigit():
        return filtered_records

    if int(limit_count) > len(filtered_records):
        filtered_records = filtered_records + data_records
    return filtered_records[: int(limit_count)]


def get_jss_data(request):
    records_all = []
    data = get_all_data(records_all, 1)

    # 获取筛选参数
    start_id = request.GET.get("start_id", "")
    limit_count = request.GET.get("limit_count", "")
    partno_all = partno.objects.all()

    # 遍历每条记录
    for record in data["records"]:
        record["partno_na_list"] = []
        # 初始化该记录的零件列表
        if "partList" in record:
            # 遍历零件列表
            for part in record["partList"]:
                if "teilnr" in part:
                    # 查询零件号对应的完整信息
                    part_info = partno_all.filter(partno=part["teilnr"]).first()
                    if part_info:
                        # 使用点表示法访问对象属性，而不是字典访问方式
                        if part_info.parttype == "左侧":
                            # 将查询到的零件信息添加到record对象中
                            record["partname_left"] = part_info.partname
                            record["parttype_left"] = part_info.parttype
                            record["partColor_left"] = part_info.partColor
                            record["partCode_left"] = part_info.partCode
                            record["car_type_left"] = part_info.car_type
                            record["partno_ascii_left"] = part_info.partno_ascii
                            record["partno_left"] = part_info.partno

                        elif part_info.parttype == "右侧":
                            # 将查询到的零件信息添加到record对象中
                            record["partname_right"] = part_info.partname
                            record["parttype_right"] = part_info.parttype
                            record["partColor_right"] = part_info.partColor
                            record["partCode_right"] = part_info.partCode
                            record["car_type_right"] = part_info.car_type
                            record["partno_ascii_right"] = part_info.partno_ascii
                            record["partno_right"] = part_info.partno
                    else:
                        record["partno_na_list"].append(part["teilnr"])

    # 倒序
    data["records"].reverse()

    # 应用筛选逻辑
    filtered_records = data["records"]

    # 应用筛选和限制
    filtered_records = filter_records_by_start_id(filtered_records, start_id, data)
    filtered_records = limit_records_count(
        filtered_records, limit_count, data["records"]
    )
    # 更新数据集
    data["records"] = filtered_records
    data["filtered_count"] = len(filtered_records)

    return render(
        request,
        "jssp/index.html",
        {
            "data": data,
            "filter_params": {"start_id": start_id, "limit_count": limit_count},
        },
    )


def get_test_data(request):
    # 使用 Django 的 BASE_DIR 来获取正确的文件路径
    json_path = os.path.join(settings.BASE_DIR, "jssp", "res.json")
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"records": []}

    # 获取筛选参数
    start_id = request.GET.get("start_id", "")
    limit_count = request.GET.get("limit_count", "")

    partno_all = partno.objects.all()

    # 遍历每条记录
    for record in data["records"]:
        record["partno_na_list"] = []
        # 初始化该记录的零件列表
        if "partList" in record:
            # 遍历零件列表
            for part in record["partList"]:
                if "teilnr" in part:
                    # 查询零件号对应的完整信息
                    part_info = partno_all.filter(partno=part["teilnr"]).first()
                    if part_info:
                        # 使用点表示法访问对象属性，而不是字典访问方式
                        if part_info.parttype == "左侧":
                            # 将查询到的零件信息添加到record对象中
                            record["partname_left"] = part_info.partname
                            record["parttype_left"] = part_info.parttype
                            record["partColor_left"] = part_info.partColor
                            record["partCode_left"] = part_info.partCode
                            record["car_type_left"] = part_info.car_type
                            record["partno_ascii_left"] = part_info.partno_ascii
                            record["partno_left"] = part_info.partno

                        elif part_info.parttype == "右侧":
                            # 将查询到的零件信息添加到record对象中
                            record["partname_right"] = part_info.partname
                            record["parttype_right"] = part_info.parttype
                            record["partColor_right"] = part_info.partColor
                            record["partCode_right"] = part_info.partCode
                            record["car_type_right"] = part_info.car_type
                            record["partno_ascii_right"] = part_info.partno_ascii
                            record["partno_right"] = part_info.partno
                    else:
                        record["partno_na_list"].append(part["teilnr"])

    # 倒序
    data["records"].reverse()

    # 应用筛选逻辑
    filtered_records = data["records"]
    # 应用筛选和限制
    filtered_records = filter_records_by_start_id(filtered_records, start_id, data)
    filtered_records = limit_records_count(
        filtered_records, limit_count, data["records"]
    )

    # 更新数据集
    data["records"] = filtered_records
    data["filtered_count"] = len(filtered_records)
    data["total"] = len(filtered_records)
    data["current"] = 1
    data["pages"] = 1

    return render(
        request,
        "jssp/index.html",
        {
            "data": data,
            "filter_params": {"start_id": start_id, "limit_count": limit_count},
        },
    )


# 零件号管理相关视图
def parts_management(request):
    """显示零件号管理页面"""
    parts = partno.objects.all()
    return render(request, "jssp/parts_management.html", {"parts": parts})


def save_part(request):
    """保存新零件信息"""
    if request.method == "POST":
        # 从表单获取数据
        part_no = request.POST.get("partno")
        part_name = request.POST.get("partname")
        part_type = request.POST.get("parttype")
        part_color = request.POST.get("partColor")
        part_code = request.POST.get("partCode")
        car_type = request.POST.get("car_type")  # 获取车型数据
        part_ascii = request.POST.get("partno_ascii")  # 获取车型数据

        # 创建或更新零件记录
        part_id = request.POST.get("part_id")
        if part_id:  # 如果有ID，则是更新操作
            part = get_object_or_404(partno, id=part_id)
            part.partno = part_no
            part.partname = part_name
            part.parttype = part_type
            part.partColor = part_color
            part.partCode = part_code
            part.partno_ascii = part_ascii
            part.car_type = car_type  # 更新车型
            part.save()
        else:  # 否则是新建操作
            partno.objects.create(
                partno=part_no,
                partname=part_name,
                parttype=part_type,
                partColor=part_color,
                partCode=part_code,
                partno_ascii=part_ascii,
                car_type=car_type,  # 添加车型
            )

        return redirect("parts_management")

    # 如果不是POST请求，重定向到零件管理页面
    return redirect("parts_management")


def edit_part(request, part_id):
    """显示编辑零件页面"""
    part = get_object_or_404(partno, id=part_id)
    parts = partno.objects.all()
    return render(request, "jssp/parts_management.html", {"part": part, "parts": parts})


def delete_part(request, part_id):
    """删除零件"""
    part = get_object_or_404(partno, id=part_id)
    part.delete()
    return redirect("parts_management")


def quick_add_part(request):
    """快速添加零件"""
    if request.method == "POST":
        part_no = request.POST.get("partno")
        part_type = request.POST.get("parttype")
        part_color = request.POST.get("partColor", "")
        car_type = request.POST.get("car_type", "")

        # 验证必填字段
        if not part_no or not part_type:
            return JsonResponse(
                {"success": False, "message": "零件号和零件类型不能为空"}
            )

        if not part_color or not car_type:
            return JsonResponse({"success": False, "message": "颜色和车型不能为空"})

        # 检查零件是否已存在
        existing_part = partno.objects.filter(partno=part_no).first()
        if existing_part:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"零件号 {part_no} 已存在",
                    "part_id": existing_part.id,
                }
            )

        # 创建新零件
        new_part = partno.objects.create(
            partno=part_no,
            partname=f"自动添加-{part_no}",
            parttype=part_type,
            partno_ascii="",
            partColor=part_color,
            car_type=car_type,
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"零件号 {part_no} 添加成功",
                "part_id": new_part.id,
            }
        )

    return JsonResponse({"success": False, "message": "不支持的请求方法"})


def export_parts_pdf(request):
    """导出零件PDF报表"""
    # 获取筛选参数
    part_type = request.GET.get("part_type", "")
    car_type = request.GET.get("car_type", "")
    search_keyword = request.GET.get("search_keyword", "")

    # 获取所有零件
    parts_query = partno.objects.all()

    # 应用筛选条件
    if part_type:
        parts_query = parts_query.filter(parttype=part_type)
    if car_type:
        parts_query = parts_query.filter(car_type=car_type)

    # 应用搜索关键词筛选 - 对多个字段进行搜索
    if search_keyword:
        from django.db.models import Q

        parts_query = parts_query.filter(
            Q(partno__icontains=search_keyword)
            | Q(partname__icontains=search_keyword)
            | Q(partColor__icontains=search_keyword)
            | Q(partCode__icontains=search_keyword)
            | Q(partno_ascii__icontains=search_keyword)
        )

    parts_list = parts_query.order_by("partno")

    # 分离左侧和右侧零件
    left_parts = parts_list.filter(parttype="左侧")
    right_parts = parts_list.filter(parttype="右侧")

    # 创建一个HTTP响应，content_type设置为PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="parts_report.pdf"'

    # 创建PDF对象
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # 注册中文字体 - 使用复用的函数
    font_name = register_chinese_font()

    # 设置标题
    p.setFont(font_name, 20)
    p.drawCentredString(width / 2, height - 50, "零件位置报表")

    # 添加生成日期
    p.setFont(font_name, 10)
    from datetime import datetime

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p.drawRightString(width - 50, height - 70, f"生成日期: {now}")

    # 添加页眉
    p.setFont(font_name, 12)
    p.drawString(50, height - 70, "CDLH WMS零件管理系统")

    # 添加筛选条件信息（如果有）
    if part_type or car_type:
        p.setFont(font_name, 9)
        filter_text = "筛选条件: "
        if part_type:
            filter_text += f"类型={part_type} "
        if car_type:
            filter_text += f"车型={car_type}"
        p.drawString(50, height - 90, filter_text)

    # 页面计数器
    page_num = 1

    # 生成二维码函数
    def generate_qr_code(text, file_prefix):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # 创建临时文件来保存图像
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".png", prefix=file_prefix
        )
        img.save(temp_file.name)
        temp_file.close()

        return temp_file.name

    # 创建临时文件列表以便后续清理
    temp_files = []

    # 每页显示的零件数
    items_per_page = 4
    total_pages = (
        max(len(left_parts), len(right_parts)) + items_per_page - 1
    ) // items_per_page

    # 处理所有页面
    for page in range(total_pages):
        # 如果不是第一页，添加新页面
        if page > 0:
            p.showPage()
            # 重设标题
            p.setFont(font_name, 20)
            p.drawCentredString(width / 2, height - 50, "零件位置报表")
            p.setFont(font_name, 10)
            p.drawRightString(width - 50, height - 70, f"生成日期: {now}")
            p.setFont(font_name, 12)
            p.drawString(50, height - 70, "CDLH WMS零件管理系统")

            # 添加筛选条件信息（如果有）
            if part_type or car_type:
                p.setFont(font_name, 9)
                filter_text = "筛选条件: "
                if part_type:
                    filter_text += f"类型={part_type} "
                if car_type:
                    filter_text += f"车型={car_type}"
                p.drawString(50, height - 90, filter_text)

        # 添加页码
        p.setFont(font_name, 10)
        p.drawCentredString(width / 2, 30, f"第 {page+1} 页 / 共 {total_pages} 页")

        # 起始和结束索引
        start_idx = page * items_per_page
        end_idx = min(
            start_idx + items_per_page, max(len(left_parts), len(right_parts))
        )

        # 表格基础位置
        table_y = height - 100
        row_height = 120  # 每行高度

        # 绘制表头
        p.setFont(font_name, 12)
        p.setFillColor(colors.blue)
        p.drawString(60, table_y, "左侧零件")
        p.setFillColor(colors.green)
        p.drawString(350, table_y, "右侧零件")
        p.setFillColor(colors.black)

        # 绘制表头线
        p.line(50, table_y - 10, 270, table_y - 10)
        p.line(340, table_y - 10, 550, table_y - 10)

        # 绘制列标题
        p.setFont(font_name, 10)
        p.drawString(60, table_y - 25, "零件号")
        p.drawString(160, table_y - 25, "位置信息")
        p.drawString(250, table_y - 25, "二维码")

        p.drawString(350, table_y - 25, "零件号")
        p.drawString(450, table_y - 25, "位置信息")
        p.drawString(540, table_y - 25, "二维码")

        # 绘制每一行
        for i in range(start_idx, end_idx):
            row_y = table_y - 45 - (i - start_idx) * row_height

            # 绘制分隔线
            if i > start_idx:
                p.setStrokeColor(colors.lightgrey)
                p.line(50, row_y + row_height - 10, 270, row_y + row_height - 10)
                p.line(340, row_y + row_height - 10, 550, row_y + row_height - 10)
                p.setStrokeColor(colors.black)

            # 左侧零件
            if i < len(left_parts):
                left_part = left_parts[i]
                p.setFont(font_name, 10)
                p.drawString(60, row_y, left_part.partno)
                p.setFont(font_name, 8)
                p.drawString(60, row_y - 15, f"车型: {left_part.car_type or '未知'}")
                p.drawString(60, row_y - 30, f"颜色: {left_part.partColor or '未知'}")

                # 生成并绘制左侧零件的二维码
                left_qr_file = generate_qr_code(
                    f"L-{left_part.partno}", f"left_{left_part.id}_"
                )
                temp_files.append(left_qr_file)
                p.drawImage(left_qr_file, 230, row_y - 60, width=60, height=60)

            # 右侧零件
            if i < len(right_parts):
                right_part = right_parts[i]
                p.setFont(font_name, 10)
                p.drawString(350, row_y, right_part.partno)
                p.setFont(font_name, 8)
                p.drawString(350, row_y - 15, f"车型: {right_part.car_type or '未知'}")
                p.drawString(350, row_y - 30, f"颜色: {right_part.partColor or '未知'}")

                # 生成并绘制右侧零件的二维码
                right_qr_file = generate_qr_code(
                    f"R-{right_part.partno}", f"right_{right_part.id}_"
                )
                temp_files.append(right_qr_file)
                p.drawImage(right_qr_file, 520, row_y - 60, width=60, height=60)

    # 完成PDF
    p.save()

    # 获取PDF值并写入响应
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    # 清理临时文件
    for temp_file in temp_files:
        try:
            os.unlink(temp_file)
        except:
            pass

    return response


def get_test_data_for_export(request):
    """获取测试数据用于导出，与get_test_data类似但不渲染模板"""
    # 使用 Django 的 BASE_DIR 来获取正确的文件路径
    json_path = os.path.join(settings.BASE_DIR, "jssp", "res.json")
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"records": []}

    partno_all = partno.objects.all()

    # 遍历每条记录
    for record in data["records"]:
        record["partno_na_list"] = []
        # 初始化该记录的零件列表
        if "partList" in record:
            # 遍历零件列表
            for part in record["partList"]:
                if "teilnr" in part:
                    # 查询零件号对应的完整信息
                    part_info = partno_all.filter(partno=part["teilnr"]).first()
                    if part_info:
                        # 使用点表示法访问对象属性，而不是字典访问方式
                        if part_info.parttype == "左侧":
                            # 将查询到的零件信息添加到record对象中
                            record["partname_left"] = part_info.partname
                            record["parttype_left"] = part_info.parttype
                            record["partColor_left"] = part_info.partColor
                            record["partCode_left"] = part_info.partCode
                            record["car_type_left"] = part_info.car_type
                            record["partno_ascii_left"] = part_info.partno_ascii
                            record["partno_left"] = part_info.partno

                        elif part_info.parttype == "右侧":
                            # 将查询到的零件信息添加到record对象中
                            record["partname_right"] = part_info.partname
                            record["parttype_right"] = part_info.parttype
                            record["partColor_right"] = part_info.partColor
                            record["partCode_right"] = part_info.partCode
                            record["car_type_right"] = part_info.car_type
                            record["partno_ascii_right"] = part_info.partno_ascii
                            record["partno_right"] = part_info.partno
                    else:
                        record["partno_na_list"].append(part["teilnr"])

    return data


# 发运单管理相关视图函数
def delivery_order_management(request):
    """发运单管理页面"""
    # 获取所有发运单
    all_orders = delivery_order.objects.all().order_by('-order_time')
    
    context = {
        'orders': all_orders,
    }
    return render(request, 'jssp/delivery_management.html', context)

def get_delivery_order_detail(request, order_id):
    """发运单详情页面"""
    # 获取特定发运单
    try:
        order = delivery_order.objects.get(id=order_id)
        # 获取发运单明细
        details = delivery_order_detail.objects.filter(order_id=order_id)
        
        # 统计左侧和右侧零件信息
        left_partno_list = {}
        right_partno_list = {}
        err_partno_list = []
        
        for detail in details:
            if detail.left_part_no and detail.left_part_no != '-':
                if detail.left_part_no in left_partno_list:
                    left_partno_list[detail.left_part_no].append(detail.id)
                else:
                    left_partno_list[detail.left_part_no] = [detail.id]
            
            if detail.right_part_no and detail.right_part_no != '-':
                if detail.right_part_no in right_partno_list:
                    right_partno_list[detail.right_part_no].append(detail.id)
                else:
                    right_partno_list[detail.right_part_no] = [detail.id]
            
            if (not detail.left_part_no or detail.left_part_no == '-') or \
               (not detail.right_part_no or detail.right_part_no == '-'):
                err_partno_list.append(detail.id)
        
        context = {
            'order': order,
            'details': details,
            'left_parts': left_partno_list,
            'right_parts': right_partno_list,
            'err_parts': err_partno_list,
            'parts_db': partno.objects.all(),
        }
        return render(request, 'jssp/delivery_detail.html', context)
    except delivery_order.DoesNotExist:
        # 如果发运单不存在，返回列表页并显示错误
        return redirect('delivery_order_management')

# 标记发运单状态为已完成
def mark_delivery_complete(request, order_id):
    """标记发运单为已完成"""
    try:
        order = delivery_order.objects.get(id=order_id)
        order.order_status = '已完成'
        order.save()
        return redirect('delivery_order_management')
    except delivery_order.DoesNotExist:
        return redirect('delivery_order_management')

# 删除发运单及其明细
def delete_delivery_order(request, order_id):
    """删除发运单及其明细"""
    try:
        order = delivery_order.objects.get(id=order_id)
        # 删除相关明细
        # delivery_order_detail.objects.filter(order_id=order_id).delete()
        # 删除发运单
        order.delete()
        return redirect('delivery_order_management')
    except delivery_order.DoesNotExist:
        return redirect('delivery_order_management')

# 查询今天8：00到现在所有发运单的数量 如果时间是凌晨，则查询昨天8：00到现在所有发运单的数量
def get_delivery_orders_today(request):
    """查询今天8:00到现在所有发运单"""
    try:
        # 获取当前时间
        current_time = datetime.now()
        
        # 如果当前时间在凌晨，则查询昨天8：00到现在所有发运单的数量
        if current_time.hour < 8:
            start_time = (current_time - timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        else:
            start_time = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
        
        # 查询今天8:00到现在所有发运单
        orders = delivery_order.objects.filter(order_time__range=(start_time, current_time))
        return len(orders)
    except Exception as e:
        return 0

