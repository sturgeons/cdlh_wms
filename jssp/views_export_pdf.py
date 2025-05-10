# 添加一个二维码
from datetime import datetime
from io import BytesIO
import os
import platform
import tempfile
from django.http import HttpResponse
import qrcode

from .models import delivery_order, delivery_order_detail, partno

# 避免循环导入
import jssp.views as views_module

# 导入ReportLab相关库
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image as RLImage

# 从utils模块导入字体注册函数
from .utils import register_chinese_font


def generate_qr_code(text, file_prefix):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=1,  # 减小边框，使二维码更紧凑
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


def generate_delivery_order_pdf(request):
    """导出发运单PDF"""
    # 获取筛选参数
    start_id = request.GET.get("start_id", "")
    limit_count = request.GET.get("limit_count", "")

    db_partno_list = partno.objects.all()
    # 获取与首页相同的数据
    if request.GET.get("data_source", "") == "test":
        # 使用测试数据
        data = views_module.get_test_data_for_export(request)
    else:
        # 使用实际数据
        data = views_module.get_api_data(request)

    # 倒序
    data["records"].reverse()


    filtered_records = data["records"]
    
    # 应用筛选和限制
    filtered_records = views_module.filter_records_by_start_id(
        filtered_records, start_id, data
    )
    filtered_records = views_module.limit_records_count(
        filtered_records, limit_count, data["records"]
    )
    # 存储发运单到数据库 存储filtered_records 到 delivery_order_detail
    order_id = delivery_order.objects.create(
        order_time=datetime.now(),
        order_status="未完成",
        order_type="JSS调度系统",
        order_start_id=start_id,
        order_size=len(filtered_records),
    )
    for record in filtered_records:
        delivery_order_detail.objects.create(
            order_id=order_id,
            lfdnr=record.get("lfdnr", ""),
            vin=record.get("vin", ""),
            part_color=record.get("partColor_left", ""),
            car_type=record.get("car_type_left", ""),
            part_ascii=record.get("partno_ascii_left", ""),
            mzeit=record.get("mzeit", ""),
            position=record.get("pointStatus", ""),
            knr=record.get("knr", ""),
            factory=record.get("werk", ""),
            product_line=record.get("productLine", ""),
            order_no=record.get("spj", ""),
            left_part_no=record.get("partno_left", ""),
            left_part_name=record.get("partname_left", ""),
            left_part_type=record.get("parttype_left", ""),
            left_part_code=record.get("partCode_left", ""),
            left_part_ascii=record.get("partno_ascii_left", ""),
            left_part_color=record.get("partColor_left", ""),
            right_part_no=record.get("partno_right", ""),
            right_part_name=record.get("partname_right", ""),
            right_part_type=record.get("parttype_right", ""),
            right_part_code=record.get("partCode_right", ""),
            right_part_ascii=record.get("partno_ascii_right", ""),
            right_part_color=record.get("partColor_right", ""),
        )

    # 创建一个HTTP响应，content_type设置为PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="jss_table_data.pdf"'

    # 使用横版模式
    buffer = BytesIO()
    width, height = landscape(A4)  # 注意这里使用landscape翻转了宽高
    p = canvas.Canvas(buffer, pagesize=landscape(A4))

    # 注册中文字体
    font_name = register_chinese_font()

    # 表头数据
    headers_left = [
        "#",
        "序列号",
        "零件类别",
        "颜色",
        "序号",
        "生产订单",
        "送货时间",
        
        "左侧",
    ]
    headers_right = [
        "#",
        "序列号",
        "零件类别",
        "颜色",
        "序号",
        "生产订单",
        "送货时间",
        "右侧",
    ]

    # 处理行数据
    rows_left = []
    rows_right = []
    rows_index = 0
    left_partno_list = {}
    right_partno_list = {}
    err_partno_list = []
    right_flow_str = ""
    left_flow_str = ""

    for record in filtered_records:
        rows_index += 1
        l_partno = record.get("partno_left", "-")
        r_partno = record.get("partno_right", "-")
        row = [
            str(rows_index),
            str(record.get("lfdnr", "")),
            record.get("vin", ""),
            record.get("knr", ""),
            # str(record.get("pointStatus", "")),
            # str(record.get("mzeit", "")),
            str(record.get("supplierReceiveTime", "")),
            # record.get("werk", ""),
            # record.get("productLine", ""),
            # record.get("spj", ""),
        ]
        if l_partno == "-" or r_partno == "-":
            err_partno_list.append([rows_index, record.get("partno_na_list", [])])
            if l_partno == "-":
                left_flow_str += "--"
            if r_partno == "-":
                right_flow_str += "--"
        else:
            left_flow_str += db_partno_list.filter(partno=l_partno).first().partno_ascii
            right_flow_str += (
                db_partno_list.filter(partno=r_partno).first().partno_ascii
            )

            if l_partno in left_partno_list:
                left_partno_list[l_partno].append(rows_index)
            else:
                left_partno_list[l_partno] = [rows_index]

            if r_partno in right_partno_list:
                right_partno_list[r_partno].append(rows_index)
            else:
                right_partno_list[r_partno] = [rows_index]
        p_l = row + [l_partno]
        p_l.insert(2, record.get("partname_left", "-"))
        p_l.insert(3, record.get("partColor_left", "-"))
        p_r = row + [r_partno]
        p_r.insert(2, record.get("partname_right", "-"))
        p_r.insert(3, record.get("partColor_right", "-"))

        rows_left.append(p_l)
        rows_right.append(p_r)

    # 在右上角绘制二维码
    # 创建二维码
    left_qr_file = generate_qr_code(left_flow_str, "left_qr_file")
    right_qr_file = generate_qr_code(right_flow_str, "right_qr_file")
    qr_size = 75  # 增大二维码尺寸

    # 设置表格参数
    margin_left = 30
    margin_top = 60
    margin_right = 30
    margin_bottom = 40  

    available_width = width - margin_left - margin_right
    available_height = height - margin_top - margin_bottom

    # 定义列宽比例
    col_width_ratios = [
        0.1,
        0.1,
        0.15,
        0.1,
        0.15,
        0.1,
        0.15,
        0.15,
    ]
    col_widths = [available_width * ratio for ratio in col_width_ratios]

    # 每页可显示的行数
    row_height = 18  # 将默认行高从25降低到20
    header_height = 20  # 将表头行高从30降低到25
    rows_per_page = int((available_height - header_height) / row_height)

    # 计算总页数（包括第一页标题页）
    table_pages = (
        (len(rows_left) + len(rows_right) + rows_per_page - 1) // rows_per_page
        if rows_left
        else 1
    )
    total_pages = 2 + table_pages  # 总页数 = 1个标题页 + 表格页数
    if len(err_partno_list) > 0:
        total_pages += 1

    # 初始化当前页为第1页
    current_page = 1

    if len(err_partno_list) > 0:
        # 绘制第一页 - 仅包含标题和二维码
        p.setFont(font_name, 20)  # 增大第一页标题字体
        p.drawCentredString(
            width / 2, height - 60, "当前零件号没有配置完全 请配置完再导出"
        )
        filter_info_y = height - 100
        p.setFont(font_name, 12)
        filter_info_y -= 20
        p.drawString(50, filter_info_y, f"没有排序信息位置")
        filter_info_y -= 20
        for e_p in err_partno_list:
            p.drawString(50, filter_info_y, f"{e_p[0]}：{e_p[1]}")
            filter_info_y -= 20
        # 结束返回报告
        p.showPage()
        current_page += 1
        filter_info_y = height - 60

    p.setFont(font_name, 16)  # 增大第一页标题字体
    p.drawCentredString(
        width / 2, height - 30, "JSS调度系统数据表   No:" + str(order_id.id)
    )

    # 添加生成日期和筛选信息
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p.setFont(font_name, 12)
    filter_info_y = height - 60
    p.drawString(
        50,
        filter_info_y,
        f"起始业务: {start_id} 显示数量: {limit_count} 生成日期: {now} 总记录数: {len(filtered_records)}",
    )

    filter_info_y -= 20
    p.setLineWidth(0.5)
    p.line(50, filter_info_y + 10, available_width, filter_info_y + 10)
    filter_info_y -= 10
    p.drawString(50, filter_info_y, f"左侧产品排序信息：")
    filter_info_y -= 20
    p.drawImage(
        left_qr_file,
        width - qr_size - 60,
        filter_info_y - qr_size / 2 - 2,
        width=qr_size,
        height=qr_size,
    )
    for l_p in left_partno_list:
        p.drawString(
            50,
            filter_info_y,
            f"零件号：{l_p}，数量：{len(left_partno_list[l_p])}, 零件名称：{db_partno_list.filter(partno=l_p).first().partname}，颜色：{db_partno_list.filter(partno=l_p).first().partColor}",
        )
        filter_info_y -= 20
        # 将整数列表转换为字符串列表，确保至少两位宽度，不足的用空格补齐
        str_list = [f"{num:>2}" for num in left_partno_list[l_p]]
        # 自动换行
        for i in range(0, len(str_list), 24):
            p.drawString(50, filter_info_y, f"{'、'.join(str_list[i:i+24])}")
            filter_info_y -= 20

    # 添加页码
    p.setFont(font_name, 10)
    p.drawCentredString(width / 2, 30, f"第 {current_page} 页 / 共 {total_pages} 页")
    p.drawString(50, 30, "供应商编码: 0C81FAW-VWC01 ")
    p.drawString(width - 188, 30, f"打印时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 结束第一页
    p.showPage()

    # 增加当前页码
    current_page += 1
    filter_info_y = height - 60

    # 绘制第一页 - 仅包含标题和二维码
    p.setFont(font_name, 16)  # 增大第一页标题字体
    p.drawCentredString(
        width / 2, height - 30, "JSS调度系统数据表   No:" + str(order_id.id)
    )

    # 添加生成日期和筛选信息
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p.setFont(font_name, 12)
    filter_info_y = height - 60
    p.drawString(
        50,
        filter_info_y,
        f"起始业务: {start_id} 显示数量: {limit_count} 生成日期: {now} 总记录数: {len(filtered_records)}",
    )

    filter_info_y -= 20
    p.setLineWidth(0.5)
    p.line(50, filter_info_y + 10, available_width, filter_info_y + 10)
    filter_info_y -= 10

    p.drawString(50, filter_info_y, f"右侧产品排序信息：")
    filter_info_y -= 20
    p.drawImage(
        right_qr_file,
        width - qr_size - 60,
        filter_info_y - qr_size / 2 - 2,
        width=qr_size,
        height=qr_size,
    )
    for r_p in right_partno_list:
        # 自动换行
        p.drawString(
            50,
            filter_info_y,
            f"零件号：{r_p}，数量：{len(right_partno_list[r_p])}, 零件名称：{db_partno_list.filter(partno=r_p).first().partname}，颜色：{db_partno_list.filter(partno=r_p).first().partColor}",
        )
        filter_info_y -= 20
        # 将整数列表转换为字符串列表，确保至少两位宽度，不足的用空格补齐
        str_list = [f"{num:>2}" for num in right_partno_list[r_p]]
        # 自动换行
        for i in range(0, len(str_list), 24):
            p.drawString(50, filter_info_y, f"{'、'.join(str_list[i:i+24])}")
            filter_info_y -= 20

    # 添加页码
    p.setFont(font_name, 10)
    p.drawCentredString(width / 2, 30, f"第 {current_page} 页 / 共 {total_pages} 页")
    p.drawString(50, 30, "供应商编码: 0C81FAW-VWC01 ")
    #打印时间
    p.drawString(width - 188, 30, f"打印时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 结束第一页
    p.showPage()
    # 从第三页开始绘制表格-左侧数据

    # 获取今天是第几个订单
    today_order_count = views_module.get_delivery_orders_today(request)+1

    # 增加当前页码
    current_page += 1

    row_index = 0

    # 绘制所有数据页面
    while row_index < len(rows_left):
        # 当前页可绘制的行数
        current_page_rows = min(rows_per_page, len(rows_left) - row_index)

        # 绘制表格标题
        p.setFont(font_name, 16)
        p.drawCentredString(width / 2, height - 30, "JSS调度系统数据表")

       

        p.drawCentredString(
            width - 148,
            height - 30,
            f"第______车   第______架",
        )
         # 绘制订单号
        p.setFont(font_name, 55)
        p.drawString(50, height - 50, f"左：{today_order_count}")

        # 绘制表头
        y = height - margin_top
        x = margin_left

        # 设置边框线宽
        p.setLineWidth(0.5)

        # 先绘制整个表格的外边框
        table_height = header_height + (current_page_rows * row_height)
        p.rect(margin_left, y - table_height, available_width, table_height)

        # 设置表头背景
        p.setFillColor(colors.lightblue)
        p.rect(
            x,
            y - header_height,
            available_width,
            header_height,
            fill=True,
            stroke=False,
        )
        p.setFillColor(colors.black)

        # 绘制表头文字和垂直网格线
        p.setFont(font_name, 10)  # 降低表头字体大小
        x = margin_left
        for i, header in enumerate(headers_left):
            # 绘制表头文字
            p.drawCentredString(
                x + col_widths[i] / 2, y - header_height / 2 - 3, header
            )  # 稍微上移表头文本
            x += col_widths[i]

            # 绘制垂直网格线(除了最后一列)
            if i < len(headers_left) - 1:
                p.line(x, y, x, y - table_height)

        # 绘制表头底部水平线(加粗)
        p.setLineWidth(1)
        p.line(
            margin_left,
            y - header_height,
            margin_left + available_width,
            y - header_height,
        )
        p.setLineWidth(0.5)

        # 绘制表格数据和水平网格线
        y = height - margin_top - header_height
        for i in range(current_page_rows):
            current_row = rows_left[row_index + i]

            # 绘制水平网格线(除了最后一行)
            if i < current_page_rows - 1:
                p.line(
                    margin_left,
                    y - row_height,
                    margin_left + available_width,
                    y - row_height,
                )

            # 绘制单元格内容
            x = margin_left
            for j, cell in enumerate(current_row):
                p.setFont(font_name, 10)  # 降低单元格字体大小

                col_width = col_widths[j]

                # 绘制文本（左对齐，垂直居中）
                text_y = (
                    y - row_height / 2 - 3
                )  # 移除额外的-3偏移，使文本在缩小的行中居中
                
                p.drawCentredString(x + col_width / 2, text_y, cell)
          

                x += col_widths[j]

            y -= row_height

        # 添加页码
        p.setFont(font_name, 10)
        p.drawCentredString(
            width / 2, 30, f"第 {current_page} 页 / 共 {total_pages} 页"
        )
        p.drawString(50, 30, "供应商编码: 0C81FAW-VWC01 ")
        p.drawString(width - 188, 30, f"打印时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 下一页
        p.showPage()
        current_page += 1
        row_index += current_page_rows

    # 从第三页开始绘制表格-右侧数据
    row_index = 0

    # 绘制所有数据页面
    while row_index < len(rows_right):
        # 当前页可绘制的行数
        current_page_rows = min(rows_per_page, len(rows_right) - row_index)

        # 绘制表格标题
        p.setFont(font_name, 16)
        p.drawCentredString(width / 2, height - 30, "JSS调度系统数据表")
        
         # 打印时间
        p.drawCentredString(
            width - 148,
            height - 30,
            f"第______车   第______架",)

        # 绘制订单号
        p.setFont(font_name, 55)
        p.drawString(50, height - 50, f"右：{today_order_count}")

       
        
        # 绘制表头
        y = height - margin_top
        x = margin_left

        # 设置边框线宽
        p.setLineWidth(0.5)

        # 先绘制整个表格的外边框
        table_height = header_height + (current_page_rows * row_height)
        p.rect(margin_left, y - table_height, available_width, table_height)

        # 设置表头背景
        p.setFillColor(colors.lightblue)
        p.rect(
            x,
            y - header_height,
            available_width,
            header_height,
            fill=True,
            stroke=False,
        )
        p.setFillColor(colors.black)

        # 绘制表头文字和垂直网格线
        p.setFont(font_name, 10)  # 降低表头字体大小
        x = margin_left
        for i, header in enumerate(headers_right):
            # 绘制表头文字
            p.drawCentredString(
                x + col_widths[i] / 2, y - header_height / 2 - 3, header
            )  # 稍微上移表头文本
            x += col_widths[i]

            # 绘制垂直网格线(除了最后一列)
            if i < len(headers_right) - 1:
                p.line(x, y, x, y - table_height)

        # 绘制表头底部水平线(加粗)
        p.setLineWidth(1)
        p.line(
            margin_left,
            y - header_height,
            margin_left + available_width,
            y - header_height,
        )
        p.setLineWidth(0.5)

        # 绘制表格数据和水平网格线
        y = height - margin_top - header_height
        for i in range(current_page_rows):
            current_row = rows_right[row_index + i]

            # 绘制水平网格线(除了最后一行)
            if i < current_page_rows - 1:
                p.line(
                    margin_left,
                    y - row_height,
                    margin_left + available_width,
                    y - row_height,
                )

            # 绘制单元格内容
            x = margin_left
            for j, cell in enumerate(current_row):
                p.setFont(font_name, 10)  # 降低单元格字体大小

                col_width = col_widths[j]

                # 绘制文本（左对齐，垂直居中）
                text_y = (
                    y - row_height / 2 - 3
                )  # 移除额外的-3偏移，使文本在缩小的行中居中
         
                p.drawCentredString(x + col_width / 2, text_y, cell)
                

                x += col_widths[j]

            y -= row_height

        # 添加页码
        p.setFont(font_name, 10)
        p.drawCentredString(
            width / 2, 30, f"第 {current_page} 页 / 共 {total_pages} 页"
        )
        p.drawString(50, 30, "供应商编码: 0C81FAW-VWC01 ")
        p.drawString(width - 188, 30, f"打印时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 下一页
        p.showPage()
        current_page += 1
        row_index += current_page_rows

    # 完成PDF
    p.save()

    # 获取PDF值并写入响应
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    # 清理临时文件
    try:
        os.unlink(left_qr_file)
        os.unlink(right_qr_file)
    except:
        pass

    return response
