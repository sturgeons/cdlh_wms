import os
import platform
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册中文字体函数
def register_chinese_font():
    """注册中文字体并返回字体名称"""
    system = platform.system()
    font_paths = []
    
    if system == 'Windows':
        # Windows系统的字体路径
        font_paths = [
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'simsun.ttc'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'simhei.ttf'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'msyh.ttc')
        ]
    else:
        # Linux/Ubuntu系统的中文字体路径
        font_paths = [
            '/usr/share/fonts/truetype/arphic/uming.ttc',  # 文泉驿Unicode明体
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # 文泉驿正黑
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Noto Sans CJK
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Droid Sans
            '/usr/share/fonts/truetype/arphic/ukai.ttc',  # AR PL UKai
            '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc'  # 文泉驿微米黑
        ]
    
    # 尝试逐个注册字体，直到成功
    font_name = 'Helvetica'  # 默认字体
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                if 'simsun' in font_path.lower() or 'uming' in font_path.lower():
                    font_name = 'SimSun'
                elif 'wqy-zenhei' in font_path.lower():
                    font_name = 'WQY-ZenHei'
                elif 'wqy-microhei' in font_path.lower():
                    font_name = 'WQY-MicroHei'
                elif 'notosans' in font_path.lower():
                    font_name = 'NotoSans'
                elif 'droid' in font_path.lower():
                    font_name = 'DroidSans'
                elif 'simhei' in font_path.lower() or 'ukai' in font_path.lower():
                    font_name = 'SimHei'
                elif 'msyh' in font_path.lower():
                    font_name = 'MicrosoftYaHei'
                else:
                    font_name = 'ChineseFont'
                
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                print(f"成功注册中文字体: {font_path}")
                return font_name
        except Exception as e:
            print(f"注册字体失败 {font_path}: {str(e)}")
            continue
    
    # 如果所有字体都注册失败
    print("警告: 无法注册中文字体，将使用默认字体。中文可能无法正确显示。")
    return font_name 