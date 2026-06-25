# Settlement Forms

结算报审单批量生成工具。

> 本项目的公开版本已迁移至独立仓库：
> https://github.com/yuyuezhou0806/settlement-forms

将 Excel 中的结构化结算信息写入标准 Word 模板，减少重复录入、人员名称错误和格式偏差。

[在线使用](http://1.15.170.85/settlement/)

## 功能

- 上传 Excel 数据表
- 解析项目及人员字段
- 批量填充 Word 模板
- 下载生成结果
- 保留运行结果和错误信息

## 技术

`Python` · `FastAPI` · `openpyxl` · `python-docx`

## 本地运行

```bash
pip install fastapi uvicorn python-multipart openpyxl python-docx pandas
python web_app.py
```

## 数据安全

公开源码不包含真实业务 Excel、Word 模板、生成文件、服务器密码和运行日志。部署密码通过环境变量 `SETTLEMENT_SSH_PASSWORD` 提供。

## Status

线上系统持续可用，最近整理于 2026-06。
