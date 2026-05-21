"""
剪贴板监控 + 自动解析脚本
用法: python clipboard_watcher.py
然后每次在 QQ 里选中聊天记录 Ctrl+C 复制，脚本会自动捕获并解析入库
"""
import time
import sys
import os

# Windows 剪贴板读取
if sys.platform == 'win32':
    import win32clipboard
    import win32con
else:
    print("此脚本仅支持 Windows")
    sys.exit(1)

from parser import MapleTradeParser, format_price_result

parser = MapleTradeParser()
last_clipboard = ""


def get_clipboard_text():
    """读取剪贴板文本"""
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return data
        win32clipboard.CloseClipboard()
    except Exception:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
    return ""


def process_clipboard(text: str):
    """处理剪贴板内容"""
    if not text or len(text) < 10:
        return

    # 简单过滤：至少包含一行看起来像交易的消息
    lines = text.split('\n')
    trade_lines = [l for l in lines if '出' in l or '收' in l]
    if len(trade_lines) < 1:
        return

    print(f"\n检测到 {len(trade_lines)} 行疑似交易记录，正在解析...")

    records = parser.parse_text(text, source="clipboard")
    saved = parser.save_records(records)

    if saved > 0:
        print(f"✓ 成功入库 {saved} 条交易记录")
        # 显示解析到的道具概览
        items = set(r.item_name for r in records)
        print(f"  涉及道具: {', '.join(list(items)[:5])}")
        if len(items) > 5:
            print(f"  等共 {len(items)} 种道具")
    else:
        print("未识别出交易记录（格式可能不对）")


def query_loop():
    """查询模式"""
    print("\n输入道具名查询价格，或输入 'exit' 退出:")
    while True:
        try:
            keyword = input("> ").strip()
            if keyword.lower() in ('exit', 'quit', 'q'):
                break
            if not keyword:
                continue
            result = parser.query_price(keyword)
            print(format_price_result(result))
        except KeyboardInterrupt:
            break
    print("再见")


def main():
    print("=" * 50)
    print("冒险岛交易群 - 剪贴板监控")
    print("=" * 50)
    print("1. 在 QQ 里选中聊天记录，Ctrl+C 复制")
    print("2. 本脚本自动捕获并解析入库")
    print("3. 按 Ctrl+C 停止监控，进入查询模式")
    print("=" * 50)

    # 先显示当前统计
    stats = parser.stats()
    print(f"\n当前数据库: {stats['items']} 种道具, {stats['total_records']} 条记录")
    print("开始监控剪贴板...\n")

    global last_clipboard
    last_clipboard = get_clipboard_text()

    try:
        while True:
            time.sleep(1)
            current = get_clipboard_text()
            if current and current != last_clipboard:
                last_clipboard = current
                process_clipboard(current)
    except KeyboardInterrupt:
        print("\n\n监控已停止")
        query_loop()


if __name__ == "__main__":
    main()
