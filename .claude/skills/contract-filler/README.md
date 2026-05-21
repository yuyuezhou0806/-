# 合同自动填充工具

从上海市建设工程项目信息报送系统的网页截图自动识别项目信息，填入Word建设工程检测合同模板，保持原有格式（下划线等）。

## 两种使用方式

### 方式一：OCR全自动（推荐）

把网页截图保存为图片，直接运行脚本自动识别并填入：

```bash
# 命令行
python contract_filler_ocr.py screenshot.png

# 或双击 run_ocr.bat，然后选择截图图片
# 或把图片拖到 run_ocr.bat 图标上
```

**OCR版会自动：**
1. 用 PaddleOCR 识别截图中的文字
2. 提取字段（建设单位、施工单位、工程名称、地址、报建编号、建筑面积等）
3. 自动填入 Word 合同模板
4. 输出填充好的合同文件

### 方式二：配置文件模式（备用）

如果OCR识别效果不好，或需要手动调整字段：

```bash
# 1. 修改 config.json 中的字段值
# 2. 运行
python contract_filler.py config.json
# 或双击 run.bat
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `contract_filler_ocr.py` | **OCR全自动版** — 截图→识别→填入 |
| `contract_filler.py` | **配置版** — 读取config.json填入 |
| `run_ocr.bat` | OCR版双击启动器（支持拖放图片） |
| `run.bat` | 配置版双击启动器 |
| `config.json` | 字段映射配置模板 |

## 安装依赖

```bash
pip install paddlepaddle paddleocr pywin32
```

## 字段映射规则

| 截图中的字段 | 填入的合同字段 |
|-------------|--------------|
| 建设单位 | 甲方（委托单位）、建设/实施单位、见证单位 |
| 施工单位 | 施工单位 |
| 设计单位 | 设计单位 |
| 监理单位 | （合同模板中没有，跳过） |
| 勘察单位 | （合同模板中没有，跳过） |
| 工程名称 / 项目名称 | 工程名称 |
| 建设地址 / 建设地点 | 工程地址 |
| 报建编号 | 工程报建编号 |
| 所属区县（从地址推导） | 工程所属区县 |
| 建筑面积 | 建筑面积（㎡） |
| 合同价格 / 总投资 | 工程投资额、工程建安费 |
| 发证机关（推导质监站） | 质监站/监管机构 |

## 合同模板位置

默认模板路径：
```
C:\Users\admin\Desktop\合同生成\空白合同【房建】（2021版）.doc
```

可在运行时用 `--template` 参数指定其他模板：
```bash
python contract_filler_ocr.py screenshot.png --template "其他模板.doc"
```

## 仍需手动处理的

- **工程性质**：政府投资 / 非政府投资（打勾）
- **总承包单位**：截图通常没有
- **甲方联系信息**（最后一页盖章处）：地址、法定代表人、银行账号、统一社会信用代码等
- **合同编号**（封面）：和报建编号一致
- **检测类别**：验收检测 / 平行检测（确认勾选）
- **检测项目**：第一条的具体内容（默认保留模板内容，或用 `--replace` 替换）

## 命令行参数

### contract_filler_ocr.py

```bash
python contract_filler_ocr.py screenshot.png [选项]

选项:
  -t, --template PATH    指定合同模板路径
  -o, --output NAME      指定输出文件名
  -s, --save-config      保存识别的config.json
  -d, --dry-run          只显示识别结果，不填入合同
```

### 示例

```bash
# 基本用法
python contract_filler_ocr.py "C:\Users\admin\Desktop\截图.png"

# 指定模板和输出名
python contract_filler_ocr.py screenshot.png -t "市政合同模板.doc" -o "市政项目-已填.doc"

# 干运行，只看识别结果
python contract_filler_ocr.py screenshot.png -d
```

## 技术说明

- **OCR引擎**：PaddleOCR（中文识别效果好）
- **Word操作**：win32com（保持原有格式，包括下划线）
- **字段提取**：正则表达式匹配 + 智能推导（如从地址推导区县、从发证机关推导质监站）
