# Contract Automation Suite

合同信息提取与文档自动化原型。

> 本项目的公开版本已迁移至独立仓库：
> https://github.com/yuyuezhou0806/contract-automation-suite

项目用于从截图和业务资料中识别工程字段，辅助完成合同信息录入、模板填充和文档生成。

## 功能

- 用户登录与任务管理
- 图片上传与 OCR 字段识别
- 合同信息校对和编辑
- 模板化文档生成
- 历史任务查询

## 技术

`Python` · `FastAPI` · `OCR` · `SQLite` · `HTML/CSS/JavaScript`

## 运行

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Status

这是早期业务原型，当前保留用于展示 OCR 与合同流程自动化思路。新的文档生成能力已逐步整合到检测行业 Agent 中。

## Privacy

公开仓库不应包含真实合同数据库、客户资料、上传文件、服务器日志或部署凭证。
