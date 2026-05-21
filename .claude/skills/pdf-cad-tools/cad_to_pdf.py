#!/usr/bin/env python3
"""CAD (.dxf) 转 PDF 工具"""

import argparse
import glob
import os
import sys


def dxf_to_pdf(dxf_path, pdf_path=None, dpi=300):
    """将单个 DXF 文件转换为 PDF"""
    import ezdxf
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    if not os.path.exists(dxf_path):
        print(f"[X] 文件不存在: {dxf_path}")
        return False

    if pdf_path is None:
        pdf_path = os.path.splitext(dxf_path)[0] + ".pdf"

    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # 获取图纸边界
        try:
            import ezdxf.bbox
            bounds = ezdxf.bbox.extents(msp)
            min_x, min_y, _ = bounds.extmin
            max_x, max_y, _ = bounds.extmax
            width = max(max_x - min_x, 1)
            height = max(max_y - min_y, 1)
            figsize = (width / 25.4, height / 25.4)
            fig = plt.figure(figsize=figsize)
        except Exception:
            print(f"[!] 无法获取图纸边界，使用默认尺寸: {dxf_path}")
            fig = plt.figure(figsize=(11.69, 8.27))

        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()

        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(msp)

        fig.savefig(pdf_path, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)

        print(f"[OK] {dxf_path} -> {pdf_path}")
        return True

    except Exception as e:
        print(f"[X] 转换失败 {dxf_path}: {e}")
        return False


def batch_convert(pattern, dpi=300):
    """批量转换匹配的文件"""
    files = glob.glob(pattern)
    if not files:
        print(f"[!] 未找到匹配文件: {pattern}")
        return

    success = 0
    for f in files:
        if dxf_to_pdf(f, dpi=dpi):
            success += 1

    print(f"\n[Done] {success}/{len(files)} 个文件转换成功")


def main():
    parser = argparse.ArgumentParser(description="CAD (DXF) 转 PDF 工具")
    parser.add_argument("input", help="输入文件或通配符（如 *.dxf）")
    parser.add_argument("-o", "--output", help="输出PDF路径（单文件模式）")
    parser.add_argument("--dpi", type=int, default=300, help="输出DPI（默认300）")
    parser.add_argument("--batch", action="store_true", help="批量模式")
    args = parser.parse_args()

    if args.batch or '*' in args.input or '?' in args.input:
        batch_convert(args.input, dpi=args.dpi)
    else:
        dxf_to_pdf(args.input, args.output, dpi=args.dpi)


if __name__ == "__main__":
    main()
