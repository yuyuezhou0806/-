import os
import re
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract

# 1. 配置环境（图片型PDF需设置Tesseract路径，Windows示例）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 2. 定义PDF文件夹路径（替换为你的PDF存放地址）
pdf_folder = r'C:\Users\admin\PyCharmMiscProject'

# 3. 定义正则表达式模式，用于匹配"报告编号"及其后面的数字
# 匹配"报告编号"后面的数字，支持可能的分隔符如冒号、空格等
pattern = r'报告编号[:：\s]*(\d+)'

# 4. 遍历文件夹中的所有PDF
for filename in os.listdir(pdf_folder):
    if filename.endswith('.pdf'):
        pdf_path = os.path.join(pdf_folder, filename)
        new_filename = ""  # 存储提取的报告编号

        # 5. 读取PDF内容（先尝试直接提取文本，失败则用OCR）
        try:
            # 方案A：直接提取文本型PDF的内容
            reader = PdfReader(pdf_path)
            text = ""
            # 尝试读取前3页内容，增加找到报告编号的概率
            for page in reader.pages[:3]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

            # 搜索报告编号
            match = re.search(pattern, text)
            if match:
                new_filename = f"报告编号{match.group(1)}"

        except Exception as e:
            print(f"{filename} 文本提取失败，尝试OCR: {str(e)}")
            # 方案B：图片型PDF用OCR识别
            try:
                from pdf2image import convert_from_path

                # 转换前3页为图片
                pages = convert_from_path(pdf_path, 500, first_page=1, last_page=3)
                text = ""
                for page_image in pages:
                    # 对每一页进行OCR识别
                    page_text = pytesseract.image_to_string(page_image, lang='chi_sim')
                    text += page_text

                # 搜索报告编号
                match = re.search(pattern, text)
                if match:
                    new_filename = f"报告编号{match.group(1)}"

            except Exception as ocr_e:
                print(f"{filename} OCR处理失败: {str(ocr_e)}")

        # 6. 清理文件名特殊字符并重命名
        if new_filename:
            invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
            for char in invalid_chars:
                new_filename = new_filename.replace(char, '')  # 删除特殊字符

            new_filepath = os.path.join(pdf_folder, f"{new_filename}.pdf")

            # 处理重复文件名
            counter = 1
            while os.path.exists(new_filepath):
                new_filepath = os.path.join(pdf_folder, f"{new_filename}_{counter}.pdf")
                counter += 1

            os.rename(pdf_path, new_filepath)
            print(f"成功重命名：{filename} → {os.path.basename(new_filepath)}")
        else:
            print(f"跳过：{filename}（未找到报告编号）")
