#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键提取网页元素信息工具
运行后会自动抓取页面上的所有关键元素
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time


def extract_elements():
    """提取网页元素信息"""
    driver = webdriver.Chrome()

    try:
        print("正在打开网页...")
        driver.get('http://192.168.99.91/')

        # 等待页面加载
        time.sleep(3)

        print("\n" + "="*60)
        print("提取到的元素信息：")
        print("="*60)

        elements_info = []

        # 1. 提取所有按钮
        print("\n【按钮类元素】")
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        for i, btn in enumerate(buttons[:20]):  # 只显示前20个
            try:
                text = btn.text.strip() or btn.get_attribute('innerText') or '无文字'
                elem_id = btn.get_attribute('id') or '无ID'
                elem_class = btn.get_attribute('class') or '无CLASS'

                if text and text != '无文字':
                    info = f"按钮{i}: 文字='{text}' | ID='{elem_id}' | CLASS='{elem_class[:50]}...'"
                    print(info)
                    elements_info.append({
                        'type': 'button',
                        'text': text,
                        'id': elem_id,
                        'class': elem_class,
                        'selector': f"//button[contains(text(), '{text}')]" if '无ID' in elem_id else f"By.ID, '{elem_id}'"
                    })
            except:
                pass

        # 2. 提取所有输入框
        print("\n【输入框类元素】")
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        for i, inp in enumerate(inputs[:10]):
            try:
                placeholder = inp.get_attribute('placeholder') or '无提示'
                elem_id = inp.get_attribute('id') or '无ID'
                elem_class = inp.get_attribute('class') or '无CLASS'
                elem_type = inp.get_attribute('type') or 'text'

                if placeholder != '无提示':
                    info = f"输入框{i}: 提示='{placeholder}' | ID='{elem_id}' | TYPE='{elem_type}'"
                    print(info)
                    elements_info.append({
                        'type': 'input',
                        'placeholder': placeholder,
                        'id': elem_id,
                        'class': elem_class,
                        'selector': f"By.CSS_SELECTOR, 'input[placeholder=\"{placeholder}\"]')" if '无ID' in elem_id else f"By.ID, '{elem_id}'"
                    })
            except:
                pass

        # 3. 提取包含特定文字的元素（菜单、链接等）
        print("\n【菜单/链接类元素】")
        keywords = ['项目管理', '查询方案', '关联生成', '确定', '提交', '保存', '新增', '删除']
        for keyword in keywords:
            try:
                elems = driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                for elem in elems[:3]:  # 每种只取前3个
                    tag = elem.tag_name
                    elem_id = elem.get_attribute('id') or '无ID'
                    elem_class = elem.get_attribute('class') or '无CLASS'

                    info = f"'{keyword}': 标签={tag} | ID='{elem_id}' | CLASS='{elem_class[:30]}'"
                    print(info)
                    elements_info.append({
                        'type': 'menu',
                        'keyword': keyword,
                        'tag': tag,
                        'id': elem_id,
                        'class': elem_class
                    })
            except:
                pass

        # 保存到文件
        print("\n" + "="*60)
        print("正在保存到文件...")

        # 保存为JSON（方便程序读取）
        with open('element_info.json', 'w', encoding='utf-8') as f:
            json.dump(elements_info, f, ensure_ascii=False, indent=2)

        # 保存为文本（方便人工查看）
        with open('element_info.txt', 'w', encoding='utf-8') as f:
            f.write("网页元素提取报告\n")
            f.write("="*60 + "\n\n")
            for elem in elements_info:
                f.write(f"类型: {elem.get('type', 'unknown')}\n")
                if 'text' in elem:
                    f.write(f"文字: {elem['text']}\n")
                if 'keyword' in elem:
                    f.write(f"关键词: {elem['keyword']}\n")
                f.write(f"ID: {elem.get('id', '无')}\n")
                f.write(f"CLASS: {elem.get('class', '无')[:50]}\n")
                if 'selector' in elem:
                    f.write(f"推荐选择器: {elem['selector']}\n")
                f.write("-"*40 + "\n\n")

        print("✓ 已保存到 element_info.json（程序用）")
        print("✓ 已保存到 element_info.txt（人工查看）")
        print("\n" + "="*60)
        print("提取完成！请查看生成的文件。")
        print("="*60)

        return elements_info

    except Exception as e:
        print(f"出错了: {e}")
        return []

    finally:
        input("\n按回车键关闭浏览器...")
        driver.quit()


if __name__ == '__main__':
    print("网页元素自动提取工具")
    print("="*60)
    print("\n这个工具会：")
    print("1. 自动打开 http://192.168.99.91/")
    print("2. 抓取所有按钮、输入框、菜单的ID和class")
    print("3. 保存到 element_info.txt 文件中")
    print("\n请确保：")
    print("- 已安装 Chrome 浏览器")
    print("- 已安装 ChromeDriver")
    print("- 网页可以正常访问")
    print("="*60 + "\n")

    input("准备好后按回车键开始...")
    extract_elements()
