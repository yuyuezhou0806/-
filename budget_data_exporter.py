#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收入预算数据抓取工具
抓取收入大项和含税金额两列数据
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class BudgetDataExporter:
    """预算数据导出器"""

    def __init__(self, base_url="http://192.168.99.91"):
        self.base_url = base_url
        self.driver = None
        self.wait = None
        self.data = []

    def start_browser(self):
        """启动浏览器"""
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        # options.add_argument('--headless')  # 无头模式，需要时可开启

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
        print("浏览器已启动")

    def login(self, username=None, password=None):
        """登录系统（如果需要）"""
        self.driver.get(f"{self.base_url}/#/personal/common/402823817d7e8763017d7ebd53350075")
        print("已打开页面，请手动登录（如果需要）")
        print("登录完成后，按 Enter 键继续...")
        input()

    def switch_to_income_tab(self):
        """切换到收入预算tab"""
        try:
            # 根据截图，tab文字是"收入预算"
            income_tab = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='收入预算']"))
            )
            income_tab.click()
            time.sleep(2)
            print("已切换到收入预算tab")
        except TimeoutException:
            print("已在收入预算tab或找不到tab")

    def get_total_pages(self):
        """获取总页数"""
        try:
            # 找分页组件，通常包含"共 X 页"或页码按钮
            pagination = self.driver.find_element(By.CLASS_NAME, "el-pagination")
            # 尝试找总页数
            page_text = pagination.text
            if "共" in page_text and "页" in page_text:
                import re
                match = re.search(r'共\s*(\d+)\s*页', page_text)
                if match:
                    return int(match.group(1))

            # 备选：数页码按钮
            page_buttons = pagination.find_elements(By.CSS_SELECTOR, "li.number")
            if page_buttons:
                return max([int(btn.text) for btn in page_buttons if btn.text.isdigit()])

        except NoSuchElementException:
            pass

        return 1  # 默认1页

    def extract_current_page_data(self):
        """提取当前页数据"""
        try:
            # 等待表格加载
            table = self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )

            # 获取所有行
            rows = table.find_elements(By.TAG_NAME, "tr")

            page_data = []
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 10:  # 确保有10列数据
                        # 收入大项是第3列（索引2）
                        # 含税金额是第8列（索引7）
                        收入大项 = cells[2].text.strip()
                        含税金额 = cells[7].text.strip()

                        # 跳过表头行和合计行
                        if 收入大项 and 收入大项 != "收入大项" and 收入大项 != "合计":
                            page_data.append({
                                '收入大项': 收入大项,
                                '含税金额': 含税金额
                            })
                except Exception as e:
                    continue

            print(f"  当前页提取到 {len(page_data)} 条数据")
            return page_data

        except TimeoutException:
            print("  等待表格超时")
            return []

    def go_to_page(self, page_num):
        """跳转到指定页"""
        try:
            # 找页码输入框或页码按钮
            # 方式1：点击页码数字
            page_btn = self.driver.find_element(
                By.XPATH, f"//li[@class='number' and text()='{page_num}']"
            )
            page_btn.click()
            time.sleep(2)
            return True
        except NoSuchElementException:
            try:
                # 方式2：找下一页按钮
                next_btn = self.driver.find_element(
                    By.CSS_SELECTOR, ".el-pagination .btn-next"
                )
                if "disabled" not in next_btn.get_attribute("class"):
                    next_btn.click()
                    time.sleep(2)
                    return True
            except:
                pass
        return False

    def export_all_data(self):
        """导出所有数据"""
        print("开始抓取数据...")

        # 切换到收入预算tab
        self.switch_to_income_tab()

        # 获取总页数
        total_pages = self.get_total_pages()
        print(f"共 {total_pages} 页数据")

        all_data = []

        for page in range(1, total_pages + 1):
            print(f"正在处理第 {page}/{total_pages} 页...")

            # 提取当前页数据
            page_data = self.extract_current_page_data()
            all_data.extend(page_data)

            # 如果不是最后一页，翻页
            if page < total_pages:
                if not self.go_to_page(page + 1):
                    print("  翻页失败，可能已到最后一页")
                    break

        self.data = all_data
        print(f"\n共抓取到 {len(all_data)} 条数据")

    def save_to_excel(self, filename="收入预算数据.xlsx"):
        """保存到Excel"""
        if not self.data:
            print("没有数据可保存")
            return

        df = pd.DataFrame(self.data)
        df.to_excel(filename, index=False)
        print(f"数据已保存到: {filename}")

        # 同时打印到控制台
        print("\n数据预览:")
        print(df.to_string(index=False))

    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")


def main():
    """主函数"""
    exporter = BudgetDataExporter()

    try:
        # 1. 启动浏览器
        exporter.start_browser()

        # 2. 打开页面并登录
        exporter.login()

        # 3. 抓取所有数据
        exporter.export_all_data()

        # 4. 保存到Excel
        exporter.save_to_excel()

    except Exception as e:
        print(f"出错了: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 5. 关闭浏览器
        input("\n按 Enter 键关闭浏览器...")
        exporter.close()


if __name__ == '__main__':
    main()
