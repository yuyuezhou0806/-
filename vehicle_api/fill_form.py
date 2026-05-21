#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动填充表单脚本
功能：将右侧显示的信息自动填写到左侧表单中
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
import time
import re


# ========== 配置区域 ==========
# 右侧信息（可以修改这里的数据）
PROJECT_DATA = {
    "报建编号": "2503CN0025",
    "工程名称": "2025年精品小区（茅台花苑）住宅修缮工程",
    "工地": "--",
    "合同流水号": "2025016343",
    "合同登记号": "2025014790",
    "委托单位名称": "上海同济工程项目管理咨询有限公司",
    "委托单位地址": "上海崇明区城桥镇东门路101号228室",
    "委托单位联系人": "李工",
    "委托单位联系电话": "13524598875",
    "委托单位联系人手机": "13524598875",
    "检测单位名称": "上海雷谷建筑科技有限公司",
    "检测单位地址": "上海市松江区洞泾镇洞薛路651弄100号1幢101室",
    "检测单位会员编号": "0133",
    "检测单位联系人": "薛鹏骏",
    "检测单位联系电话": "13816098933",
    "是否是监理平行检测": "否",
    "标段": "",
    "工程性质": "修缮",
    "工程地址": "茅台路500弄2、4、5、6、7、9号",
    "工程所属区县": "长宁区",
    "工程收变质监站名称": "长宁区住宅修缮工程管理中心",
    "建设单位名称": "上海同济工程项目管理咨询有限公司",
    "设计单位名称": "上海市政工程设计研究总院（集团）有限公司",
    "见证单位名称": "上海科安建设监理有限公司",
    "施工单位名称": "上海金鹿建设（集团）有限公司"
}

# 延时配置
WAIT_TIME = 0.5  # 每个操作后的等待时间（秒）
# ==============================


def fill_form():
    """自动填充表单主函数"""
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    wait = WebDriverWait(driver, 10)

    try:
        print("正在打开网页...")
        # 请替换为实际的网址
        url = input("请输入网页地址（直接回车使用默认）：").strip()
        if not url:
            url = "http://shcetcd.com/"  # 根据截图推测的网址

        driver.get(url)
        print(f"已打开: {url}")
        print("请手动登录并进入到表单页面，然后按回车继续...")
        input()

        print("\n开始自动填充...\n")

        # 1. 填充报建编号
        try:
            field = wait.until(EC.presence_of_element_located((By.NAME, "txtBaoJianBianHao")))
            field.clear()
            field.send_keys(PROJECT_DATA["报建编号"])
            print(f"✓ 报建编号: {PROJECT_DATA['报建编号']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 报建编号填充失败: {e}")

        # 2. 填充工程名称
        try:
            field = driver.find_element(By.NAME, "txtGongChengMingCheng")
            field.clear()
            field.send_keys(PROJECT_DATA["工程名称"])
            print(f"✓ 工程名称: {PROJECT_DATA['工程名称']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 工程名称填充失败: {e}")

        # 3. 选择工地（下拉框）
        try:
            if PROJECT_DATA["工地"] and PROJECT_DATA["工地"] != "--":
                select = Select(driver.find_element(By.NAME, "ddlGongDi"))
                select.select_by_visible_text(PROJECT_DATA["工地"])
                print(f"✓ 工地: {PROJECT_DATA['工地']}")
                time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 工地选择失败: {e}")

        # 4. 填充委托单位名称
        try:
            field = driver.find_element(By.NAME, "txtWeiTuoDanWeiMingCheng")
            field.clear()
            field.send_keys(PROJECT_DATA["委托单位名称"])
            print(f"✓ 委托单位名称: {PROJECT_DATA['委托单位名称']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 委托单位名称填充失败: {e}")

        # 5. 填充委托单位地址
        try:
            field = driver.find_element(By.NAME, "txtWeiTuoDanWeiDiZhi")
            field.clear()
            field.send_keys(PROJECT_DATA["委托单位地址"])
            print(f"✓ 委托单位地址: {PROJECT_DATA['委托单位地址']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 委托单位地址填充失败: {e}")

        # 6. 填充委托单位联系人
        try:
            field = driver.find_element(By.NAME, "txtWeiTuoDanWeiLianXiRen")
            field.clear()
            field.send_keys(PROJECT_DATA["委托单位联系人"])
            print(f"✓ 委托单位联系人: {PROJECT_DATA['委托单位联系人']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 委托单位联系人填充失败: {e}")

        # 7. 填充委托单位电话
        try:
            field = driver.find_element(By.NAME, "txtWeiTuoDanWeiDianHua")
            field.clear()
            field.send_keys(PROJECT_DATA["委托单位联系电话"])
            print(f"✓ 委托单位电话: {PROJECT_DATA['委托单位联系电话']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 委托单位电话填充失败: {e}")

        # 8. 填充委托单位联系人手机
        try:
            field = driver.find_element(By.NAME, "txtWeiTuoDanWeiShouJi")
            field.clear()
            field.send_keys(PROJECT_DATA["委托单位联系人手机"])
            print(f"✓ 委托单位联系人手机: {PROJECT_DATA['委托单位联系人手机']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 委托单位联系人手机填充失败: {e}")

        # 9. 选择检测单位（下拉框+查找）
        try:
            # 先尝试选择下拉框
            select = Select(driver.find_element(By.NAME, "ddlJianCeDanWei"))
            select.select_by_visible_text(PROJECT_DATA["检测单位名称"])
            print(f"✓ 检测单位: {PROJECT_DATA['检测单位名称']}")
            time.sleep(WAIT_TIME)
        except:
            # 如果下拉框没有，尝试点击查找按钮输入
            try:
                search_btn = driver.find_element(By.XPATH, "//input[@value='查找' and contains(@onclick, 'JianCeDanWei')]")
                search_btn.click()
                time.sleep(1)
                # 在弹窗中输入单位名称
                popup_input = driver.find_element(By.XPATH, "//input[contains(@id, 'JianCeDanWei')]")
                popup_input.send_keys(PROJECT_DATA["检测单位名称"])
                time.sleep(0.5)
            except Exception as e:
                print(f"✗ 检测单位选择失败: {e}")

        # 10. 填充检测单位联系人
        try:
            field = driver.find_element(By.NAME, "txtJianCeDanWeiLianXiRen")
            field.clear()
            field.send_keys(PROJECT_DATA["检测单位联系人"])
            print(f"✓ 检测单位联系人: {PROJECT_DATA['检测单位联系人']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 检测单位联系人填充失败: {e}")

        # 11. 填充检测单位联系电话
        try:
            field = driver.find_element(By.NAME, "txtJianCeDanWeiDianHua")
            field.clear()
            field.send_keys(PROJECT_DATA["检测单位联系电话"])
            print(f"✓ 检测单位联系电话: {PROJECT_DATA['检测单位联系电话']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 检测单位联系电话填充失败: {e}")

        # 12. 选择标段
        try:
            if PROJECT_DATA["标段"]:
                select = Select(driver.find_element(By.NAME, "ddlBiaoDuan"))
                select.select_by_visible_text(PROJECT_DATA["标段"])
                print(f"✓ 标段: {PROJECT_DATA['标段']}")
                time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 标段选择失败: {e}")

        # 13. 选择工程性质
        try:
            select = Select(driver.find_element(By.NAME, "ddlGongChengXingZhi"))
            select.select_by_visible_text(PROJECT_DATA["工程性质"])
            print(f"✓ 工程性质: {PROJECT_DATA['工程性质']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 工程性质选择失败: {e}")

        # 14. 填充工程地址
        try:
            field = driver.find_element(By.NAME, "txtGongChengDiZhi")
            field.clear()
            field.send_keys(PROJECT_DATA["工程地址"])
            print(f"✓ 工程地址: {PROJECT_DATA['工程地址']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 工程地址填充失败: {e}")

        # 15. 选择工程所属区县
        try:
            select = Select(driver.find_element(By.NAME, "ddlSuoShuQuXian"))
            select.select_by_visible_text(PROJECT_DATA["工程所属区县"])
            print(f"✓ 工程所属区县: {PROJECT_DATA['工程所属区县']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 工程所属区县选择失败: {e}")

        # 16. 选择工程收变质监站名称
        try:
            select = Select(driver.find_element(By.NAME, "ddlZhiJianZhan"))
            select.select_by_visible_text(PROJECT_DATA["工程收变质监站名称"])
            print(f"✓ 工程收变质监站: {PROJECT_DATA['工程收变质监站名称']}")
            time.sleep(WAIT_TIME)
        except Exception as e:
            print(f"✗ 工程收变质监站选择失败: {e}")

        print("\n" + "="*50)
        print("✅ 表单填充完成！")
        print("="*50)

        # 询问是否自动点击保存
        save = input("\n是否自动点击'新增'按钮保存？(y/n): ").strip().lower()
        if save == 'y':
            try:
                save_btn = driver.find_element(By.XPATH, "//input[@value='新增' or @value='保存']")
                save_btn.click()
                print("✓ 已点击保存")
            except:
                print("✗ 未找到保存按钮，请手动点击")

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

    finally:
        print("\n浏览器保持打开状态，请手动关闭")
        input("按回车键关闭浏览器...")
        driver.quit()


if __name__ == "__main__":
    print("="*50)
    print("自动填充表单工具")
    print("="*50)
    print("\n使用说明：")
    print("1. 运行此脚本")
    print("2. 在打开的浏览器中手动登录")
    print("3. 进入到需要填写的表单页面")
    print("4. 按回车键开始自动填充")
    print("5. 检查填充结果，必要时手动调整")
    print("\n" + "="*50)

    input("\n准备好后按回车键开始...")
    fill_form()
