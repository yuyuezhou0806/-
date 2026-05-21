#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BPM 项目汇报自动化工具 - 优化版本（修复版）
"""

import logging
import os
import sys
import time
import traceback
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Callable
from functools import wraps

import openpyxl
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    ElementNotInteractableException, WebDriverException
)


# ==================== 配置 ====================
@dataclass
class Config:
    """应用配置"""
    BASE_URL: str = 'http://bpm.chinajyy.net/#/passport/login'
    USERNAME: str = 'Z0343'
    PASSWORD: str = ''
    DEFAULT_UPLOAD_FILE: str = r"C:\Users\admin\PyCharmMiscProject\2026年2月签单.pdf"
    LOG_DIR: str = 'logs'
    SCREENSHOT_DIR: str = 'screenshots'
    IMPLICIT_WAIT: int = 10
    EXPLICIT_WAIT: int = 15
    POLL_FREQUENCY: float = 0.5
    ITEMS_PER_PAGE: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0


def retry_on_exception(max_retries: int = 3, delay: float = 2.0,
                       exceptions: Tuple = (Exception,)):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logging.warning(f"{func.__name__} 第 {attempt + 1} 次尝试失败: {e}，{delay}秒后重试...")
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


class LoggerMixin:
    """日志混入类"""
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)


class BasePage(LoggerMixin):
    """基础页面类"""

    def __init__(self, driver: webdriver.Chrome, config: Config):
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(
            driver,
            config.EXPLICIT_WAIT,
            poll_frequency=config.POLL_FREQUENCY
        )

    def find(self, locator: Tuple[By, str], timeout: int = None) -> WebElement:
        """查找元素"""
        wait = WebDriverWait(self.driver, timeout or self.config.EXPLICIT_WAIT)
        return wait.until(EC.presence_of_element_located(locator))

    def find_all(self, locator: Tuple[By, str], timeout: int = None) -> List[WebElement]:
        """查找所有匹配元素"""
        wait = WebDriverWait(self.driver, timeout or self.config.EXPLICIT_WAIT)
        return wait.until(EC.presence_of_all_elements_located(locator))

    def click(self, locator: Tuple[By, str], timeout: int = None):
        """点击元素"""
        wait = WebDriverWait(self.driver, timeout or self.config.EXPLICIT_WAIT)
        element = wait.until(EC.element_to_be_clickable(locator))
        element.click()
        return element

    def input_text(self, locator: Tuple[By, str], text: str, clear: bool = True):
        """输入文本"""
        element = self.click(locator)
        if clear:
            element.clear()
        element.send_keys(str(text))
        return element

    def double_click(self, locator: Tuple[By, str]):
        """双击元素"""
        element = self.find(locator)
        ActionChains(self.driver).double_click(element).perform()

    def select_dropdown(self, dropdown_locator: Tuple[By, str], option_text: str):
        """选择下拉框选项"""
        self.click(dropdown_locator)
        time.sleep(0.3)
        option_locator = (By.XPATH, f"//li[contains(text(), '{option_text')]")
        self.click(option_locator)

    def is_element_present(self, locator: Tuple[By, str], timeout: int = 3) -> bool:
        """检查元素是否存在"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False


class LoginPage(BasePage):
    """登录页面"""
    USERNAME_INPUT = (By.CLASS_NAME, 'ant-input')
    LOGIN_BUTTON = (By.XPATH, "//form//button[contains(@class, 'ant-btn')]")

    def login(self, username: str, password: str):
        """执行登录"""
        self.logger.info(f"正在登录，用户: {username}")
        self.driver.get(self.config.BASE_URL)

        self.input_text(self.USERNAME_INPUT, username)

        # 输入密码
        password_inputs = self.driver.find_elements(By.XPATH, "//input[@type='password']")
        if password_inputs:
            password_inputs[0].send_keys(password)

        self.click(self.LOGIN_BUTTON)
        time.sleep(3)
        self.logger.info("登录成功")
        return HomePage(self.driver, self.config)


class HomePage(BasePage):
    """首页"""
    SELF_APP_MENU = (By.XPATH, "//header//li[2]//header-app//span[contains(@class, 'ng-star-inserted')]")
    PROJECT_MGMT_ITEM = (By.XPATH, "//div[contains(@class, 'app-item')]//small[text()='项目管理']")

    def navigate_to_project_mgmt(self):
        """导航到项目管理"""
        self.logger.info("导航到项目管理")
        self.click(self.SELF_APP_MENU)
        time.sleep(1)
        self.click(self.PROJECT_MGMT_ITEM)
        time.sleep(3)
        return ProjectListPage(self.driver, self.config)


class ProjectListPage(BasePage):
    """项目列表页面"""
    QUERY_SCHEME_BTN = (By.XPATH, "//button[.//i[@nztype='search']]")
    ADD_FILTER_BTN = (By.XPATH, "//a[.//i[@nztype='plus']]")
    FILTER_VALUE_INPUT = (By.XPATH, "(//input[@placeholder='比较值'])[last()]")
    CONFIRM_FILTER_BTN = (By.XPATH, "//button[@nztype='primary' and contains(text(), '确定')]")
    PROJECT_ROW = (By.XPATH, "//table//tbody//tr")
    RELATION_GENERATE_MENU = (By.XPATH, "//button[contains(text(), '关联生成')]")

    @retry_on_exception(max_retries=2, delay=1.0)
    def search_project(self, project_num: str) -> bool:
        """搜索项目"""
        self.logger.info(f"搜索项目编号: {project_num}")

        self.click(self.QUERY_SCHEME_BTN)
        time.sleep(1)
        self.click(self.ADD_FILTER_BTN)
        time.sleep(0.5)

        # 选择字段 - 项目编码
        field_select = (By.XPATH, "(//nz-select[@nzplaceholder='选择字段'])[last()]")
        self.click(field_select)
        time.sleep(0.3)
        project_code_option = (By.XPATH, "//li[contains(text(), '项目编码')]")
        self.click(project_code_option)

        # 选择比较符 - 等于
        operator_select = (By.XPATH, "(//nz-select[@nzplaceholder='选择比较符'])[last()]")
        self.click(operator_select)
        time.sleep(0.3)
        equals_option = (By.XPATH, "//li[contains(text(), '等于')]")
        self.click(equals_option)

        # 输入项目编号
        self.input_text(self.FILTER_VALUE_INPUT, project_num)

        # 点击确定
        self.click(self.CONFIRM_FILTER_BTN)
        time.sleep(2)

        rows = self.driver.find_elements(*self.PROJECT_ROW)
        if len(rows) == 0:
            self.logger.warning(f"未找到项目: {project_num}")
            return False

        self.logger.info(f"找到项目，共 {len(rows)} 条记录")
        return True

    def select_first_project(self):
        """选择第一个项目"""
        self.logger.info("选择第一个项目")
        row = (By.XPATH, "//table//tbody//tr[1]//td[2]")
        self.click(row)
        time.sleep(1)

    def open_work_report_form(self):
        """打开工作汇报单表单"""
        self.logger.info("打开工作汇报单")

        self.click(self.RELATION_GENERATE_MENU)
        time.sleep(0.5)

        work_report = (By.XPATH, "//li[contains(text(), '生成项目工作汇报单')]")
        self.click(work_report)
        time.sleep(0.5)

        submenu = (By.XPATH, "//a[contains(text(), '生成项目工作汇报单')]")
        if self.is_element_present(submenu, timeout=2):
            self.click(submenu)
            time.sleep(1)

        return WorkReportFormPage(self.driver, self.config)


class WorkReportFormPage(BasePage):
    """工作汇报单表单页面"""
    LABOR_FEE_SELECT = (By.XPATH, "//nz-form-label[contains(., '有无劳务费')]/following::nz-select[1]")
    LABOR_DETAIL_TAB = (By.XPATH, "//div[contains(@class, 'ant-tabs-tab') and contains(text(), '劳务费明细')]")
    WORK_HOUR_TAB = (By.XPATH, "//div[contains(@class, 'ant-tabs-tab') and contains(text(), '人工工时')]")
    ADD_WORKER_BTN = (By.XPATH, "//button[.//i[@nztype='plus']]")
    WORKER_POPUP_ROW = (By.XPATH, "//div[contains(@class, 'pop-window')]//table//tbody//tr")
    PAGE_INFO = (By.XPATH, "//div[contains(@class, 'pop-window')]//li[contains(@class, 'ant-pagination-total-text')]")
    WORKLOAD_ADJUST_CHECKBOX = (By.XPATH, "//label[contains(., '工作量调整')]//input[@type='checkbox']")
    CURRENT_WORKLOAD_INPUT = (By.XPATH, "//nz-form-label[contains(., '本期汇报金额')]/following::input[1]")
    REMARK_TEXTAREA = (By.XPATH, "//textarea[@placeholder='请输入备注']")
    FILE_UPLOAD_INPUT = (By.XPATH, "//input[@type='file']")
    AUDIT_BTN = (By.XPATH, "//button[contains(., '审核') or contains(., '提交')]")

    def set_labor_fee(self, has_labor_fee: bool):
        """设置有无劳务费"""
        option_text = "有" if has_labor_fee else "无"
        self.logger.info(f"设置劳务费: {option_text}")
        self.select_dropdown(self.LABOR_FEE_SELECT, option_text)
        time.sleep(0.5)

    def add_labor_fee_detail(self, amount: float):
        """添加劳务费明细"""
        self.logger.info(f"添加劳务费明细: {amount}")
        self.click(self.LABOR_DETAIL_TAB)
        time.sleep(0.5)
        self.click(self.ADD_WORKER_BTN)
        time.sleep(0.5)

        worker_input = (By.XPATH, "//div[contains(@class, 'pop-window')]//tbody//tr//td[2]//div/div")
        self.click(worker_input)
        time.sleep(0.3)

        edit_icon = (By.XPATH, "//div[contains(@class, 'pop-window')]//tbody//tr//td[2]//span[contains(@class, 'edit')]")
        self.click(edit_icon)
        time.sleep(0.5)

        first_worker = (By.XPATH, "//div[contains(@class, 'pop-window')]//table//tbody//tr[1]//td[1]")
        self.double_click(first_worker)
        time.sleep(0.5)

        amount_input = (By.XPATH, "//tbody//tr//td[4]//input")
        self.input_text(amount_input, str(amount))

    def set_remark(self, text: str = "项目在建中"):
        """设置备注"""
        self.logger.info(f"设置备注: {text}")
        self.input_text(self.REMARK_TEXTAREA, text)

    def get_worker_count(self) -> int:
        """获取人员数量"""
        try:
            page_info = self.find(self.PAGE_INFO)
            text = page_info.text
            match = re.search(r'(\d+)', text)
            if match:
                return int(match.group(1))
        except:
            pass

        rows = self.driver.find_elements(*self.WORKER_POPUP_ROW)
        return len(rows)

    def add_worker_hours(self, worker_index: int, hours: float):
        """添加单个工人的工时"""
        self.logger.debug(f"为第 {worker_index} 个工人设置工时: {hours}")

        worker_cell = (By.XPATH, f"//tbody[@id='childTableBody-ProWorkReportEW']//tr[{worker_index}]//td[2]//div/div")
        self.click(worker_cell)
        time.sleep(0.3)

        edit_icon = (By.XPATH, f"//tbody[@id='childTableBody-ProWorkReportEW']//tr[{worker_index}]//td[2]//span[contains(@class, 'edit')]")
        self.click(edit_icon)
        time.sleep(0.5)

        total_count = self.get_worker_count()
        items_per_page = 30

        page_num = (worker_index - 1) // items_per_page + 1
        row_on_page = (worker_index - 1) % items_per_page + 1

        for _ in range(page_num - 1):
            try:
                next_btn = (By.XPATH, "//div[contains(@class, 'pop-window')]//li[contains(@class, 'ant-pagination-next')]//a")
                self.click(next_btn)
                time.sleep(0.5)
            except:
                break

        worker_item = (By.XPATH, f"//div[contains(@class, 'pop-window')]//table//tbody//tr[{row_on_page}]//td[1]")
        self.double_click(worker_item)
        time.sleep(0.5)

        hour_input = (By.XPATH, f"//tbody[@id='childTableBody-ProWorkReportEW']//tr[{worker_index}]//td[5]//input")
        self.input_text(hour_input, str(hours))

    def add_all_worker_hours(self, hours: float):
        """为所有工人添加工时"""
        self.logger.info("切换到人工工时标签")
        self.click(self.WORK_HOUR_TAB)
        time.sleep(0.5)

        self.click(self.ADD_WORKER_BTN)
        time.sleep(0.5)

        worker_cell = (By.XPATH, "//tbody[@id='childTableBody-ProWorkReportEW']//tr[1]//td[2]//div/div")
        self.click(worker_cell)
        time.sleep(0.3)

        edit_icon = (By.XPATH, "//tbody[@id='childTableBody-ProWorkReportEW']//tr[1]//td[2]//span[contains(@class, 'edit')]")
        self.click(edit_icon)
        time.sleep(1)

        total_workers = self.get_worker_count()
        self.logger.info(f"共有 {total_workers} 个工人")

        first_worker = (By.XPATH, "//div[contains(@class, 'pop-window')]//table//tbody//tr[1]//td[1]")
        self.double_click(first_worker)
        time.sleep(0.5)

        for i in range(1, total_workers + 1):
            try:
                self.add_worker_hours(i, hours)
            except Exception as e:
                self.logger.error(f"为第 {i} 个工人设置工时失败: {e}")
                raise

    def enable_workload_adjust(self):
        """启用工作量调整"""
        self.logger.info("启用工作量调整")
        checkbox = self.find(self.WORKLOAD_ADJUST_CHECKBOX)
        if not checkbox.is_selected():
            checkbox.click()
        time.sleep(0.3)

    def set_workload(self, workload: float):
        """设置本期汇报金额"""
        self.logger.info(f"设置本期汇报金额: {workload}")
        self.input_text(self.CURRENT_WORKLOAD_INPUT, str(workload))

    def upload_attachment(self, file_path: str):
        """上传附件"""
        self.logger.info(f"上传附件: {file_path}")
        if not os.path.exists(file_path):
            self.logger.warning(f"文件不存在: {file_path}")
            return

        upload_input = self.driver.find_element(*self.FILE_UPLOAD_INPUT)
        upload_input.send_keys(file_path)
        time.sleep(3)

    def submit(self):
        """提交审核"""
        self.logger.info("提交审核")
        self.click(self.AUDIT_BTN)
        time.sleep(3)


class BPMReporter(LoggerMixin):
    """BPM 汇报主控类"""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.driver: Optional[webdriver.Chrome] = None
        self._setup_logging()
        self._ensure_directories()

    def _setup_logging(self):
        """配置日志"""
        log_file = os.path.join(
            self.config.LOG_DIR,
            f"bpm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def _ensure_directories(self):
        """确保所需目录存在"""
        for directory in [self.config.LOG_DIR, self.config.SCREENSHOT_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _init_driver(self) -> webdriver.Chrome:
        """初始化 WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')

        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(self.config.IMPLICIT_WAIT)
        return driver

    def _take_screenshot(self, name: str):
        """保存截图"""
        if self.driver:
            filename = os.path.join(
                self.config.SCREENSHOT_DIR,
                f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            self.driver.save_screenshot(filename)
            self.logger.info(f"截图已保存: {filename}")

    def __enter__(self):
        """上下文管理器入口"""
        self.driver = self._init_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type:
            self.logger.error(f"发生异常: {exc_val}")
            self._take_screenshot("error")

        if self.driver:
            self.driver.quit()
            self.logger.info("浏览器已关闭")

    @retry_on_exception(max_retries=2, delay=2.0, exceptions=(WebDriverException,))
    def process_project(self, project_num: str, workload: float,
                        work_hours: float, labor_fees: float) -> bool:
        """处理单个项目"""
        self.logger.info("=" * 50)
        self.logger.info(f"开始处理项目: {project_num}")

        try:
            login_page = LoginPage(self.driver, self.config)
            home_page = login_page.login(self.config.USERNAME, self.config.PASSWORD)

            project_list_page = home_page.navigate_to_project_mgmt()

            if not project_list_page.search_project(project_num):
                self.logger.error(f"未找到项目: {project_num}")
                return False

            project_list_page.select_first_project()
            form_page = project_list_page.open_work_report_form()

            form_page.set_labor_fee(labor_fees > 0)

            if labor_fees > 0:
                form_page.add_labor_fee_detail(labor_fees)

            form_page.set_remark()
            form_page.add_all_worker_hours(work_hours)
            form_page.enable_workload_adjust()
            form_page.set_workload(workload)
            form_page.upload_attachment(self.config.DEFAULT_UPLOAD_FILE)
            form_page.submit()

            self.logger.info(f"项目 {project_num} 处理成功")
            return True

        except Exception as e:
            self.logger.error(f"处理项目 {project_num} 失败: {e}")
            self.logger.error(traceback.format_exc())
            self._take_screenshot(f"fail_{project_num}")
            return False


@dataclass
class ProjectData:
    """项目数据"""
    project_num: str
    workload: float
    work_hours: float
    labor_fees: float


def safe_float(value, default=0.0) -> float:
    """安全转换为 float"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def read_excel(filepath: str) -> List[ProjectData]:
    """读取 Excel 文件 - 修复索引越界问题"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")

    wb = openpyxl.load_workbook(filepath, data_only=True)
    sheet = wb.active

    data = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        # 修复: 检查 row 是否为 None 或长度不足
        if not row:
            continue

        # 确保至少有4个值，不足则补 None
        row_values = list(row) + [None] * (4 - len(row)) if len(row) < 4 else list(row)

        project_num = row_values[0]
        if not project_num:
            continue

        data.append(ProjectData(
            project_num=str(project_num).strip(),
            workload=safe_float(row_values[1]),
            work_hours=safe_float(row_values[2]),
            labor_fees=safe_float(row_values[3])
        ))

    return data


def write_log(log_file: str, message: str):
    """写入日志文件"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")


def main():
    """主函数"""
    excel_name = input('请输入表格名（不含扩展名）: ').strip()
    if not excel_name:
        print("错误：表格名不能为空")
        return

    excel_path = f"{excel_name}.xlsx"
    log_file = f"log_{excel_name}.txt"

    try:
        projects = read_excel(excel_path)
        print(f"共读取到 {len(projects)} 条数据")
    except FileNotFoundError:
        print(f"错误：找不到文件 {excel_path}")
        return
    except Exception as e:
        print(f"读取 Excel 失败: {e}")
        return

    success_count = 0
    fail_count = 0
    failed_projects = []

    config = Config()

    with BPMReporter(config) as reporter:
        for i, project in enumerate(projects, 1):
            print(f"\n[{i}/{len(projects)}] 正在处理: {project.project_num}")

            start_msg = f"开始: {project.project_num}, 工作量={project.workload}, 工时={project.work_hours}"
            print(start_msg)
            write_log(log_file, start_msg)

            success = reporter.process_project(
                project.project_num,
                project.workload,
                project.work_hours,
                project.labor_fees
            )

            if success:
                success_count += 1
                msg = f"成功: {project.project_num}"
                print(msg)
                write_log(log_file, msg)
            else:
                fail_count += 1
                failed_projects.append(project.project_num)
                msg = f"失败: {project.project_num}"
                print(msg)
                write_log(log_file, msg)

            if i < len(projects):
                time.sleep(2)

    summary = f"""
{'='*50}
处理完成！
总计: {len(projects)}
成功: {success_count}
失败: {fail_count}
{'='*50}
"""
    print(summary)
    write_log(log_file, summary)

    if failed_projects:
        print(f"\n失败项目列表:")
        for p in failed_projects:
            print(f"  - {p}")
            write_log(log_file, f"失败项目: {p}")


if __name__ == '__main__':
    main()
