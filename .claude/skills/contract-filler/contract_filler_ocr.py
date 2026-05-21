#!/usr/bin/env python3
"""
合同自动填充工具 (OCR版)
从网页截图自动识别项目信息，填入Word建设工程检测合同

用法:
    python contract_filler_ocr.py <截图图片路径>
    python contract_filler_ocr.py <截图图片路径> --template <合同模板路径>

示例:
    python contract_filler_ocr.py screenshot.png
    python contract_filler_ocr.py screenshot.png --template "空白合同.doc"
"""

import argparse
import json
import os
import re
import sys
import tempfile
import win32com.client


def ocr_image(image_path):
    """使用PaddleOCR识别图片文字"""
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        print("[X] PaddleOCR未安装，请先运行: pip install paddlepaddle paddleocr")
        sys.exit(1)

    print("[*] 正在识别图片文字，请稍候...")
    ocr = PaddleOCR(
        use_textline_orientation=True,
        lang='ch',
    )
    result = ocr.ocr(image_path, cls=True)

    # 提取所有文字
    texts = []
    if result and result[0]:
        for line in result[0]:
            if line:
                text = line[1][0]  # 文字内容
                confidence = line[1][1]  # 置信度
                if confidence > 0.5:  # 过滤低置信度
                    texts.append(text)

    full_text = '\n'.join(texts)
    return full_text, texts


def extract_fields(text):
    """从OCR识别文本中提取关键字段"""
    fields = {}

    # 报建编号
    m = re.search(r'报建编号[：:]\s*(\w+)', text)
    if m:
        fields['报建编号'] = m.group(1).strip()

    # 工程名称 / 项目名称
    for pattern in [r'工程名称[：:]\s*([^\n]+)', r'项目名称[：:]\s*([^\n]+)']:
        m = re.search(pattern, text)
        if m:
            fields['工程名称'] = m.group(1).strip()
            break

    # 建设地址 / 建设地点 / 工程地址
    for pattern in [r'建设地址[：:]\s*([^\n]+)', r'建设地点[：:]\s*([^\n]+)', r'工程地址[：:]\s*([^\n]+)']:
        m = re.search(pattern, text)
        if m:
            fields['建设地址'] = m.group(1).strip()
            break

    # 建设单位
    m = re.search(r'建设单位[：:]\s*([^\n]+)', text)
    if m:
        fields['建设单位'] = m.group(1).strip()

    # 施工单位
    m = re.search(r'施工单位[：:]\s*([^\n]+)', text)
    if m:
        fields['施工单位'] = m.group(1).strip()

    # 设计单位
    m = re.search(r'设计单位[：:]\s*([^\n]+)', text)
    if m:
        fields['设计单位'] = m.group(1).strip()

    # 监理单位
    m = re.search(r'监理单位[：:]\s*([^\n]+)', text)
    if m:
        fields['监理单位'] = m.group(1).strip()

    # 见证单位
    m = re.search(r'见证单位[：:]\s*([^\n]+)', text)
    if m:
        fields['见证单位'] = m.group(1).strip()

    # 勘察单位
    m = re.search(r'勘察单位[：:]\s*([^\n]+)', text)
    if m:
        fields['勘察单位'] = m.group(1).strip()

    # 建筑面积 - 多种格式
    for pattern in [
        r'建筑面积[：:]\s*([\d.]+)',
        r'建设规模.*建筑面积[：:]\s*([\d.]+)',
        r'建筑面积\D*?([\d.]+)',
    ]:
        m = re.search(pattern, text)
        if m:
            fields['建筑面积'] = m.group(1).strip()
            break

    # 合同价格 / 总投资
    for pattern in [
        r'合同价格\(万元\)[：:]\s*([\d.]+)',
        r'总投资\(万元\)[：:]\s*([\d.]+)',
        r'合同价格[：:]\s*([\d.]+)',
        r'总投资[：:]\s*([\d.]+)',
    ]:
        m = re.search(pattern, text)
        if m:
            fields['合同价格'] = m.group(1).strip()
            break

    # 所属区县 - 从地址中推导
    districts = ['奉贤区', '浦东新区', '徐汇区', '黄浦区', '静安区', '长宁区',
                 '普陀区', '虹口区', '杨浦区', '闵行区', '宝山区', '嘉定区',
                 '金山区', '松江区', '青浦区', '崇明区']
    for district in districts:
        if district in text:
            fields['所属区县'] = district
            break

    # 质监站/监管机构 - 从发证机关推导
    m = re.search(r'发证机关[：:]\s*([^\n]+)', text)
    if m:
        org = m.group(1).strip()
        if '建设' in org and '管理' in org:
            fields['质监站'] = org.replace('建设和管理委员会', '建设工程安全质量监督站')
        else:
            fields['质监站'] = org

    # 施工许可证号
    m = re.search(r'施工许可证号[：:]\s*(\w+)', text)
    if m:
        fields['施工许可证号'] = m.group(1).strip()

    # 合同工期
    m = re.search(r'合同工期[：:]\s*([^\n]+)', text)
    if m:
        fields['合同工期'] = m.group(1).strip()

    return fields


def build_contract_config(fields, template_path, output_name):
    """从提取的字段构建合同填充配置"""
    config = {
        'template_path': template_path,
        'output_name': output_name,
        'fields': {},
        'global_replaces': {},
    }

    # 建设单位 -> 甲方、建设/实施单位、见证单位
    if '建设单位' in fields:
        company = fields['建设单位']
        config['fields']['甲方（委托单位）'] = company
        config['fields']['建设/实施单位：'] = company
        config['fields']['见证单位：'] = company

    # 施工单位
    if '施工单位' in fields:
        config['fields']['施工单位：'] = fields['施工单位']

    # 设计单位
    if '设计单位' in fields:
        config['fields']['设计单位：'] = fields['设计单位']

    # 见证单位（网页表单用，Word模板里也有）
    if '见证单位' in fields:
        config['fields']['见证单位：'] = fields['见证单位']

    # 工程名称
    if '工程名称' in fields:
        config['fields']['工程名称：'] = fields['工程名称']

    # 工程地址
    if '建设地址' in fields:
        config['fields']['工程地址：'] = fields['建设地址']

    # 报建编号
    if '报建编号' in fields:
        config['fields']['工程报建编号：'] = fields['报建编号']

    # 所属区县
    if '所属区县' in fields:
        config['fields']['工程所属区县：'] = fields['所属区县']

    # 建筑面积
    if '建筑面积' in fields:
        config['fields']['建筑面积（㎡）：'] = fields['建筑面积']

    # 投资额/建安费
    if '合同价格' in fields:
        price = fields['合同价格'] + '万元'
        config['fields']['工程投资额：'] = price
        config['fields']['工程建安费：'] = price

    # 质监站
    if '质监站' in fields:
        config['fields']['质监站/监管机构：'] = fields['质监站']

    return config


def fill_contract(config):
    """使用Word COM接口填入合同"""
    template_path = config.get('template_path', '')
    output_name = config.get('output_name', '合同-已填充.doc')
    fields = config.get('fields', {})
    global_replaces = config.get('global_replaces', {})

    if not os.path.exists(template_path):
        print(f"[X] 模板文件不存在: {template_path}")
        return False

    template_dir = os.path.dirname(template_path) or '.'
    output_path = os.path.join(template_dir, output_name)

    word = win32com.client.Dispatch('Word.Application')
    word.Visible = False
    word.DisplayAlerts = False

    try:
        doc = word.Documents.Open(os.path.abspath(template_path))
        print(f"[*] 已打开模板: {os.path.basename(template_path)}")

        # 填入字段
        success = 0
        fail = 0
        for field_label, value in fields.items():
            word.Selection.HomeKey(Unit=6)
            find = word.Selection.Find
            find.ClearFormatting()
            find.Text = field_label
            find.Forward = True
            find.Wrap = 0
            find.Format = False
            find.MatchCase = False
            find.MatchWholeWord = False

            if find.Execute():
                word.Selection.Collapse(Direction=0)
                word.Selection.Font.Underline = True
                word.Selection.TypeText(value)
                word.Selection.Font.Underline = False
                success += 1
                print(f"  [OK] {field_label} -> {value[:40]}")
            else:
                fail += 1
                print(f"  [X] 未找到: {field_label}")

        # 全局替换
        for old_text, new_text in global_replaces.items():
            word.Selection.HomeKey(Unit=6)
            find = word.Selection.Find
            find.ClearFormatting()
            find.Text = old_text
            find.Replacement.Text = new_text
            find.Forward = True
            find.Wrap = 1
            find.Format = False
            find.MatchCase = False
            find.MatchWholeWord = False
            if find.Execute(Replace=2):
                print(f"  [OK] 替换: {old_text[:20]}...")

        doc.SaveAs(os.path.abspath(output_path))
        doc.Close()
        print(f"\n[OK] 合同已保存: {output_path}")
        print(f"     成功填入 {success} 个字段")
        if fail > 0:
            print(f"     {fail} 个字段未找到（模板中可能不存在）")
        return True

    except Exception as e:
        print(f"[X] 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        word.Quit()


def main():
    parser = argparse.ArgumentParser(description='从网页截图自动识别并填入建设工程检测合同')
    parser.add_argument('image', help='网页截图图片路径')
    parser.add_argument('--template', '-t', default=r'C:\Users\admin\Desktop\合同生成\空白合同【房建】（2021版）.doc',
                        help='合同模板路径')
    parser.add_argument('--output', '-o', help='输出文件名（默认从工程名称生成）')
    parser.add_argument('--save-config', '-s', action='store_true',
                        help='保存生成的config.json到临时目录')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='只显示识别结果，不填入合同')

    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"[X] 图片文件不存在: {args.image}")
        sys.exit(1)

    # Step 1: OCR识别
    full_text, texts = ocr_image(args.image)

    print("\n" + "=" * 60)
    print("  OCR识别结果")
    print("=" * 60)
    for i, text in enumerate(texts, 1):
        print(f"  {i}. {text}")

    # Step 2: 提取字段
    print("\n" + "=" * 60)
    print("  提取的字段")
    print("=" * 60)
    fields = extract_fields(full_text)
    if not fields:
        print("  [!] 未能从图片中提取到字段")
        sys.exit(1)

    for key, value in fields.items():
        print(f"  {key}: {value}")

    # Step 3: 构建配置
    project_name = fields.get('工程名称', '合同')
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', project_name)
    output_name = args.output or f"{safe_name}-已填充.doc"

    config = build_contract_config(fields, args.template, output_name)

    # Step 4: 保存config（可选）
    if args.save_config:
        config_path = os.path.join(tempfile.gettempdir(), 'contract_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"\n[*] 配置已保存: {config_path}")

    # Step 5: 只显示结果（dry-run模式）
    if args.dry_run:
        print("\n[*] 干运行模式，不填入合同")
        print("\n将要填入的字段:")
        for k, v in config['fields'].items():
            print(f"  {k} -> {v}")
        return

    # Step 6: 填入合同
    print("\n" + "=" * 60)
    print("  填入合同")
    print("=" * 60)
    fill_contract(config)


if __name__ == '__main__':
    main()
