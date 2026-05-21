#!/usr/bin/env python3
"""合同自动填充工具 - 从配置文件读取信息填入Word合同模板"""

import json
import os
import sys
import win32com.client


def load_config(config_path):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def fill_field(word_app, doc, find_text, fill_text):
    """在Word文档中找到字段并填入内容（保持下划线格式）"""
    word_app.Selection.HomeKey(Unit=6)  # wdStory
    find = word_app.Selection.Find
    find.ClearFormatting()
    find.Text = find_text
    find.Forward = True
    find.Wrap = 0  # wdFindStop
    find.Format = False
    find.MatchCase = False
    find.MatchWholeWord = False

    if find.Execute():
        word_app.Selection.Collapse(Direction=0)  # wdCollapseEnd
        word_app.Selection.Font.Underline = True  # wdUnderlineSingle
        word_app.Selection.TypeText(fill_text)
        word_app.Selection.Font.Underline = False
        return True
    return False


def replace_text(word_app, doc, find_text, replace_text):
    """全局替换文本（用于检测项目等）"""
    word_app.Selection.HomeKey(Unit=6)
    find = word_app.Selection.Find
    find.ClearFormatting()
    find.Text = find_text
    find.Replacement.Text = replace_text
    find.Forward = True
    find.Wrap = 1  # wdFindContinue
    find.Format = False
    find.MatchCase = False
    find.MatchWholeWord = False
    return find.Execute(Replace=2)  # wdReplaceAll


def fill_contract(config):
    """主填充逻辑"""
    template_path = config.get('template_path', '')
    output_name = config.get('output_name', '合同-已填充.doc')
    fields = config.get('fields', {})
    global_replaces = config.get('global_replaces', {})

    if not os.path.exists(template_path):
        print(f"[X] 模板文件不存在: {template_path}")
        return False

    # 确定输出路径
    template_dir = os.path.dirname(template_path)
    output_path = os.path.join(template_dir, output_name)

    # 打开Word
    word = win32com.client.Dispatch('Word.Application')
    word.Visible = False
    word.DisplayAlerts = False

    try:
        doc = word.Documents.Open(os.path.abspath(template_path))
        print(f"[*] 已打开模板: {template_path}")

        # 填入各个字段
        success = 0
        fail = 0
        for field_label, value in fields.items():
            if fill_field(word, doc, field_label, value):
                success += 1
                print(f"  [OK] {field_label} -> {value[:30]}")
            else:
                fail += 1
                print(f"  [X] 未找到字段: {field_label}")

        # 全局替换（如检测项目内容）
        for old_text, new_text in global_replaces.items():
            if replace_text(word, doc, old_text, new_text):
                print(f"  [OK] 替换: {old_text[:20]} -> {new_text[:20]}")
            else:
                print(f"  [!] 未找到替换文本: {old_text[:20]}")

        # 保存
        doc.SaveAs(os.path.abspath(output_path))
        doc.Close()
        print(f"\n[OK] 合同已保存: {output_path}")
        print(f"     成功填入 {success} 个字段, {fail} 个未找到")
        return True

    except Exception as e:
        print(f"[X] 错误: {e}")
        return False

    finally:
        word.Quit()


def main():
    if len(sys.argv) < 2:
        print("用法: python contract_filler.py <config.json>")
        print("示例: python contract_filler.py config.json")
        sys.exit(1)

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"[X] 配置文件不存在: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    fill_contract(config)


if __name__ == '__main__':
    main()
