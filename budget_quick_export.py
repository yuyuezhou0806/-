#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速抓取当前页收入预算数据
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def quick_export():
    """快速导出当前页数据"""

    # 启动浏览器
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 15)

    try:
        # 打开页面
        driver.get("http://192.168.99.91/#/personal/common/402823817d7e8763017d7ebd53350075")

        print("请手动登录并确保在【收入预算】tab")
        input("准备好后按 Enter 键开始抓取...")

        # 等待表格加载
        table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        # 抓取数据
        rows = table.find_elements(By.TAG_NAME, "tr")

        data = []
        for row in rows[1:]:  # 跳过表头
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 8:
                收入大项 = cells[2].text.strip()
                含税金额 = cells[7].text.strip()

                # 跳过合计行
                if 收入大项 and "合计" not in 收入大项:
                    data.append({
                        '收入大项': 收入大项,
                        '含税金额': 含税金额
                    })

        # 保存
        df = pd.DataFrame(data)
        filename = f"收入预算_{time.strftime('%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)

        print(f"\n✅ 成功抓取 {len(data)} 条数据")
        print(f"已保存到: {filename}")
        print("\n数据预览:")
        print(df)

    except Exception as e:
        print(f"出错: {e}")

    finally:
        input("\n按 Enter 关闭浏览器...")
        driver.quit()


if __name__ == '__main__':
    quick_export()
