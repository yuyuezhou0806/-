# PDF & CAD 工具集

CAD转PDF、PDF拆分/合并/批量重命名/压缩/报告的命令行工具。

## 安装依赖

```bash
pip install ezdxf pikepdf matplotlib openpyxl Pillow
```

或双击运行 `install-deps.bat`

## Windows 用户注意

如果中文输出显示乱码，在命令前加 `PYTHONIOENCODING=utf-8`：

```bash
PYTHONIOENCODING=utf-8 python cad_to_pdf.py ...
```

## 使用方式

以下命令假设你在项目根目录执行，脚本路径为 `.claude/skills/pdf-cad-tools/`。

### CAD → PDF

```bash
# 单文件
python .claude/skills/pdf-cad-tools/cad_to_pdf.py drawing.dxf -o output.pdf

# 批量（*.dxf 加引号防止 shell 展开）
python .claude/skills/pdf-cad-tools/cad_to_pdf.py "*.dxf" --batch --dpi 300
```

### PDF 拆分

```bash
python .claude/skills/pdf-cad-tools/pdf_tools.py split input.pdf -o 拆分结果/
```

### PDF 合并（支持生成报告）

```bash
# 普通合并
python .claude/skills/pdf-cad-tools/pdf_tools.py merge a.pdf b.pdf c.pdf -o merged.pdf

# 合并 + 自动生成报告（Excel + 文本）
python .claude/skills/pdf-cad-tools/pdf_tools.py merge a.pdf b.pdf c.pdf -o merged.pdf --report
```

合并报告示例：
```
============================================================
  PDF 合并报告
============================================================
生成时间: 2026-05-15 12:19:46
输出文件: 合并合同.pdf

序号  文件名                           页数      大小
------------------------------------------------------------
1     合同_甲方.pdf                     3       981.0 B
2     合同_乙方.pdf                     4       1.2 KB
3     附件_清单.pdf                     5       1.4 KB
------------------------------------------------------------
合计  3 个文件                           12 页    3.5 KB
============================================================
```

### PDF 批量重命名（支持正则）

```bash
# 先预览（不实际执行）
python .claude/skills/pdf-cad-tools/pdf_tools.py rename "old_" "new_" -d ./pdfs --dry-run

# 确认没问题后执行
python .claude/skills/pdf-cad-tools/pdf_tools.py rename "old_" "new_" -d ./pdfs
```

### PDF 提取指定页

```bash
python .claude/skills/pdf-cad-tools/pdf_tools.py extract input.pdf "5-10" -o out.pdf
```

### PDF 压缩

```bash
# 默认中等压缩
python .claude/skills/pdf-cad-tools/pdf_tools.py compress input.pdf

# 指定压缩质量
python .claude/skills/pdf-cad-tools/pdf_tools.py compress input.pdf -q low    # 高压缩
python .claude/skills/pdf-cad-tools/pdf_tools.py compress input.pdf -q high   # 低压缩
```

## 双击/拖放脚本（Windows）

| 脚本 | 功能 | 操作方式 |
|------|------|---------|
| `install-deps.bat` | 安装依赖 | 双击运行 |
| `dxf2pdf.bat` | DXF 转 PDF | 拖放 .dxf 文件 |
| `pdf-split.bat` | PDF 拆分 | 拖放 .pdf 文件 |
| `pdf-merge.bat` | PDF 合并 | 拖放多个 .pdf，可选生成报告 |
| `pdf-rename.bat` | 批量重命名 | 双击运行，交互式输入 |
| `pdf-extract.bat` | 提取页面 | 拖放 .pdf 文件 |
| `pdf-compress.bat` | PDF 压缩 | 拖放 .pdf 文件，选择压缩质量 |

## 限制

- CAD 转换仅支持 **DXF** 格式（.dwg 需先用 AutoCAD/SolidWorks 另存为 .dxf）
- PDF 操作需要文件未加密（如有密码需先解密）
- PDF 压缩主要针对图片进行，纯文字 PDF 压缩效果有限
