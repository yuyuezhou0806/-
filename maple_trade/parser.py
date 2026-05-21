import re
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class TradeRecord:
    price: float
    trade_type: str  # 'sell' = 出, 'buy' = 收
    item_name: str
    raw_text: str
    source: str = ""
    created_at: str = ""

class MapleTradeParser:
    """冒险岛交易群聊天记录解析器"""

    # 核心正则：匹配 价格+出/收+道具名
    PATTERNS = [
        # 25出彩火5个装, 3000出花海浅眠武器, 0.85出2500E
        (r'^(\d+(?:\.\d+)?)\s*出\s*(.+)$', 'sell'),
        # 收价格式: 800收屠龙刀
        (r'^(\d+(?:\.\d+)?)\s*收\s*(.+)$', 'buy'),
    ]

    # 需要过滤掉的非交易行
    SKIP_KEYWORDS = [
        '群发消息', '有需要的老板', '点头像私聊', '已被', '动画表情',
        '图片', '交易注意', 'QQ号', '不要私聊', '小心冒充',
        '进群改', '群昵称', '只允许', '禁发', '代洗',
    ]

    def __init__(self, db_path: str = "trade_prices.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化 SQLite 数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 道具表：去重后的道具名称
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                name_normalized TEXT NOT NULL,
                first_seen TEXT,
                last_seen TEXT,
                count_sell INTEGER DEFAULT 0,
                count_buy INTEGER DEFAULT 0
            )
        ''')

        # 价格记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                price REAL NOT NULL,
                trade_type TEXT NOT NULL,  -- 'sell' 叫价/出, 'buy' 收价/收
                raw_text TEXT NOT NULL,
                source TEXT,
                created_at TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        ''')

        # 索引加速查询
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_prices_item ON prices(item_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_prices_type ON prices(trade_type)
        ''')

        conn.commit()
        conn.close()

    def _normalize_item_name(self, name: str) -> str:
        """标准化道具名称，用于去重"""
        # 去掉末尾的杂项描述，保留核心道具名
        name = name.strip()
        # 去掉括号里的补充说明，但保留主名
        name = re.sub(r'\([^)]*\)$', '', name).strip()
        # 统一空格
        name = re.sub(r'\s+', '', name)
        return name.lower()

    def _should_skip(self, text: str) -> bool:
        """判断是否为非交易消息"""
        text = text.strip()
        if len(text) < 3:
            return True
        for kw in self.SKIP_KEYWORDS:
            if kw in text:
                return True
        return False

    def parse_line(self, text: str) -> Optional[TradeRecord]:
        """解析单行文本"""
        text = text.strip()
        if self._should_skip(text):
            return None

        for pattern, trade_type in self.PATTERNS:
            match = re.match(pattern, text)
            if match:
                price = float(match.group(1))
                item_name = match.group(2).strip()

                # 过滤掉明显不是道具的内容
                if len(item_name) < 2:
                    continue
                if item_name.isdigit():
                    continue

                return TradeRecord(
                    price=price,
                    trade_type=trade_type,
                    item_name=item_name,
                    raw_text=text,
                    created_at=datetime.now().isoformat()
                )

        return None

    def parse_text(self, text: str, source: str = "") -> List[TradeRecord]:
        """解析多行文本"""
        records = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            record = self.parse_line(line)
            if record:
                record.source = source
                records.append(record)
        return records

    def save_records(self, records: List[TradeRecord]):
        """保存记录到数据库"""
        if not records:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        saved = 0

        for r in records:
            normalized = self._normalize_item_name(r.item_name)

            # 插入或更新道具
            is_sell = 1 if r.trade_type == 'sell' else 0
            is_buy = 1 if r.trade_type == 'buy' else 0
            cursor.execute('''
                INSERT INTO items (name, name_normalized, first_seen, last_seen, count_sell, count_buy)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    count_sell = count_sell + ?,
                    count_buy = count_buy + ?
            ''', (r.item_name, normalized, r.created_at, r.created_at, is_sell, is_buy,
                  is_sell, is_buy))

            # 获取 item_id
            cursor.execute('SELECT id FROM items WHERE name = ?', (r.item_name,))
            item_id = cursor.fetchone()[0]

            # 插入价格记录
            cursor.execute('''
                INSERT INTO prices (item_id, price, trade_type, raw_text, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (item_id, r.price, r.trade_type, r.raw_text, r.source, r.created_at))
            saved += 1

        conn.commit()
        conn.close()
        return saved

    def query_price(self, keyword: str) -> dict:
        """查询道具价格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 模糊匹配道具名
        cursor.execute('''
            SELECT i.id, i.name, i.name_normalized
            FROM items i
            WHERE i.name_normalized LIKE ? OR i.name LIKE ?
        ''', (f'%{keyword.lower()}%', f'%{keyword}%'))

        items = cursor.fetchall()

        if not items:
            conn.close()
            return {"found": False, "keyword": keyword}

        results = []
        for item_id, item_name, _ in items:
            # 最高叫价（出）
            cursor.execute('''
                SELECT MAX(price), COUNT(*) FROM prices
                WHERE item_id = ? AND trade_type = 'sell'
            ''', (item_id,))
            max_sell, count_sell = cursor.fetchone()

            # 最高收价（收）
            cursor.execute('''
                SELECT MAX(price), COUNT(*) FROM prices
                WHERE item_id = ? AND trade_type = 'buy'
            ''', (item_id,))
            max_buy, count_buy = cursor.fetchone()

            # 最近几条记录
            cursor.execute('''
                SELECT price, trade_type, raw_text, created_at
                FROM prices
                WHERE item_id = ?
                ORDER BY created_at DESC
                LIMIT 5
            ''', (item_id,))
            recent = cursor.fetchall()

            results.append({
                "item": item_name,
                "max_sell": max_sell,
                "count_sell": count_sell or 0,
                "max_buy": max_buy,
                "count_buy": count_buy or 0,
                "recent": [
                    {"price": p, "type": "出" if t == 'sell' else "收", "text": raw, "time": ts}
                    for p, t, raw, ts in recent
                ]
            })

        conn.close()
        return {"found": True, "keyword": keyword, "results": results}

    def stats(self) -> dict:
        """数据库统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM items')
        item_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM prices')
        price_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM prices WHERE trade_type = "sell"')
        sell_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM prices WHERE trade_type = "buy"')
        buy_count = cursor.fetchone()[0]

        conn.close()

        return {
            "items": item_count,
            "total_records": price_count,
            "sell_records": sell_count,
            "buy_records": buy_count
        }


def format_price_result(result: dict) -> str:
    """格式化查询结果为可读文本"""
    if not result["found"]:
        return f'未找到 "{result["keyword"]}" 相关的交易记录'

    lines = []
    for r in result["results"]:
        lines.append(f'\n【{r["item"]}】')

        if r["count_sell"] > 0:
            lines.append(f'  最高叫价(出): {r["max_sell"]:g} ({r["count_sell"]}条记录)')
        else:
            lines.append(f'  最高叫价(出): 暂无')

        if r["count_buy"] > 0:
            lines.append(f'  最高收价(收): {r["max_buy"]:g} ({r["count_buy"]}条记录)')
        else:
            lines.append(f'  最高收价(收): 暂无')

        if r["recent"]:
            lines.append(f'  最近记录:')
            for rec in r["recent"][:3]:
                lines.append(f'    {rec["type"]} {rec["price"]:g} - {rec["text"]}')

    return '\n'.join(lines)


if __name__ == "__main__":
    import sys

    parser = MapleTradeParser()

    if len(sys.argv) < 2:
        print("用法:")
        print("  python parser.py import <聊天记录.txt>   # 导入聊天记录")
        print("  python parser.py query <道具名>          # 查询价格")
        print("  python parser.py stats                   # 查看统计")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "import" and len(sys.argv) >= 3:
        filepath = sys.argv[2]
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        records = parser.parse_text(text, source=filepath)
        saved = parser.save_records(records)
        print(f"解析完成: 从 {len(text.split(chr(10)))} 行中提取 {len(records)} 条交易记录")
        print(f"成功入库: {saved} 条")

    elif cmd == "query" and len(sys.argv) >= 3:
        keyword = sys.argv[2]
        result = parser.query_price(keyword)
        print(format_price_result(result))

    elif cmd == "stats":
        print(json.dumps(parser.stats(), indent=2, ensure_ascii=False))

    else:
        print("未知命令")
