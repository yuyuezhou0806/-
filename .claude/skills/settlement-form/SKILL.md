---
name: settlement-form
description: 项目结算报审单批量填充工具。读取Excel数据，自动填入Word模板，批量生成结算报审单。金额自动从万元转换为元，智能处理项目名称后缀避免重复。
---

# 项目结算报审单批量填充

## 功能

1. **Excel → Word 自动填充**：读取Excel数据，批量填入Word模板
2. **金额自动转换**：Excel中的万元自动转为元（×10000）
3. **智能名称拼接**：避免 "检测检测项目" 这种重复
4. **文件名规范**：`合同编号_项目名称_项目负责人.docx`

## 启动方式

### 方式一：命令行（推荐）

```bash
# 默认配置（使用同目录下的模板和Excel）
python batch_fill.py

# 指定文件
python batch_fill.py 数据.xlsx --template 模板.docx --output ./output
```

### 方式二：双击运行（Windows）

双击 `run.bat`

### 方式三：网页版

```bash
pip install fastapi uvicorn python-multipart
python web_app.py
# 打开 http://localhost:8080
```

## Excel 数据格式要求

| 列名 | 说明 |
|------|------|
| 付款单位 | 接收单位名称 |
| 合同编号（结账号） | 合同编号 |
| 项目名称 | 项目名称 |
| 实际发生总工作量(含税) | 万元单位 |
| 实际应支付检测费（含税） | 万元单位 |
| 已确认收入（含税） | 万元单位 |
| 开票金额(含税) | 万元单位 |
| 已收款金额（含税） | 万元单位 |
| 项目负责人 | 负责人姓名 |

## 触发关键词

- "结算报审单"
- "批量生成结算"
- "填充报审单"
- "结算单生成"

## 依赖安装

```bash
pip install python-docx pandas openpyxl
```
