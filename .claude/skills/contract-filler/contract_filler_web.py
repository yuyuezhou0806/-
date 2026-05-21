#!/usr/bin/env python3
"""
合同网页填充工具 - OCR 识别 → 剪贴板 JSON
从网页截图自动识别项目信息，生成 JSON 复制到剪贴板，用于 shcetia 网页表单填充

用法:
    python contract_filler_web.py <截图图片路径>
    或把图片拖到 contract_filler_web.py 上

示例:
    python contract_filler_web.py screenshot.png
"""

import argparse
import json
import os
import re
import sys


def ocr_image(image_path):
    """使用PaddleOCR识别图片文字"""
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        print("[X] PaddleOCR未安装，请先运行: pip install paddlepaddle paddleocr")
        sys.exit(1)

    print("[*] 正在识别图片文字，请稍候...")
    ocr = PaddleOCR(use_textline_orientation=True, lang='ch', show_log=False)
    result = ocr.ocr(image_path, cls=True)

    texts = []
    if result and result[0]:
        for line in result[0]:
            if line:
                text = line[1][0]
                confidence = line[1][1]
                if confidence > 0.5:
                    texts.append(text)

    return '\n'.join(texts), texts


def extract_fields(text):
    """从OCR识别文本中提取网页填充需要的5个关键字段"""
    fields = {}

    # 报建编号
    m = re.search(r'报建编号[：:]\s*(\w+)', text)
    if m:
        fields['报建编号'] = m.group(1).strip()

    # 工程名称（备用，用于生成文件名）
    for pattern in [r'工程名称[：:]\s*([^\n]+)', r'项目名称[：:]\s*([^\n]+)']:
        m = re.search(pattern, text)
        if m:
            fields['工程名称'] = m.group(1).strip()
            break

    # 工程地址（优先）/ 建设地址
    for pattern in [r'工程地址[：:]\s*([^\n]+)', r'建设地址[：:]\s*([^\n]+)', r'建设地点[：:]\s*([^\n]+)']:
        m = re.search(pattern, text)
        if m:
            fields['工程地址'] = m.group(1).strip()
            break

    # 设计单位
    m = re.search(r'设计单位[：:]\s*([^\n]+)', text)
    if m:
        fields['设计单位'] = m.group(1).strip()

    # 见证单位
    m = re.search(r'见证单位[：:]\s*([^\n]+)', text)
    if m:
        fields['见证单位'] = m.group(1).strip()

    # 施工单位
    m = re.search(r'施工单位[：:]\s*([^\n]+)', text)
    if m:
        fields['施工单位'] = m.group(1).strip()

    # 建设单位（备用，见证单位没识别到时用）
    m = re.search(r'建设单位[：:]\s*([^\n]+)', text)
    if m:
        fields['建设单位'] = m.group(1).strip()

    return fields


def set_clipboard(text):
    """设置剪贴板内容"""
    try:
        import win32clipboard
        import win32con
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        win32clipboard.CloseClipboard()
        return True
    except Exception:
        # fallback: tkinter
        try:
            import tkinter as tk
            r = tk.Tk()
            r.withdraw()
            r.clipboard_clear()
            r.clipboard_append(text)
            r.destroy()
            return True
        except Exception as e:
            print(f"[X] 剪贴板设置失败: {e}")
            return False


def show_notification(title, message):
    """弹出 Windows 气泡通知"""
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=5)
        return
    except ImportError:
        pass

    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
    except Exception:
        print(f"\n[!] {title}: {message}")


def main():
    parser = argparse.ArgumentParser(description='从网页截图识别项目信息，输出JSON到剪贴板')
    parser.add_argument('image', help='网页截图图片路径')
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"[X] 图片文件不存在: {args.image}")
        sys.exit(1)

    # Step 1: OCR识别
    full_text, texts = ocr_image(args.image)

    print("\n" + "=" * 50)
    print("  OCR 识别结果")
    print("=" * 50)
    for i, text in enumerate(texts, 1):
        print(f"  {i}. {text}")

    # Step 2: 提取字段
    print("\n" + "=" * 50)
    print("  提取的字段")
    print("=" * 50)
    all_fields = extract_fields(full_text)

    # 只取网页需要的5个字段
    web_fields = {}
    for key in ['报建编号', '工程地址', '设计单位', '见证单位', '施工单位']:
        if key in all_fields:
            web_fields[key] = all_fields[key]
            print(f"  {key}: {all_fields[key]}")
        else:
            print(f"  [X] {key}: 未识别")

    # 见证单位没识别到，用建设单位兜底
    if '见证单位' not in web_fields and '建设单位' in all_fields:
        web_fields['见证单位'] = all_fields['建设单位']
        print(f"  [兜底] 见证单位 -> 建设单位: {all_fields['建设单位']}")

    if not web_fields:
        print("\n[X] 未能提取到任何字段")
        sys.exit(1)

    # Step 3: 生成 JSON → 剪贴板
    json_str = json.dumps(web_fields, ensure_ascii=False)

    print("\n" + "=" * 50)
    print("  网页填充 JSON")
    print("=" * 50)
    print(json_str)

    if set_clipboard(json_str):
        print("\n[OK] JSON 已复制到剪贴板！")
        show_notification(
            "合同填充",
            f"已提取 {len(web_fields)} 个字段，JSON 已复制到剪贴板。\n去 shcetia 网页控制台粘贴执行。"
        )
    else:
        print("\n[!] 请手动复制上面的 JSON")

    # 同时保存到桌面，备用
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    project_name = all_fields.get('工程名称', '合同')
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', project_name)
    save_path = os.path.join(desktop, f"{safe_name}_web_fields.json")
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(web_fields, f, ensure_ascii=False, indent=2)
    print(f"[OK] 同时保存到: {save_path}")


if __name__ == '__main__':
    main()
