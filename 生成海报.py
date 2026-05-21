from PIL import Image, ImageDraw, ImageFont
import os

# ==================== 配置 ====================
OUTPUT_FILE = "python代写服务海报.png"
WIDTH, HEIGHT = 1080, 1920

# 尝试加载中文字体（不同系统）
FONT_PATHS = [
    "C:/Windows/Fonts/msyhbd.ttc",           # Windows 微软雅黑粗体
    "C:/Windows/Fonts/msyh.ttc",             # Windows 微软雅黑
    "/System/Library/Fonts/PingFang.ttc",    # Mac
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Linux
]

def get_font(size):
    """尝试加载中文字体，失败则用默认"""
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

# ==================== 颜色配置 ====================
BG_TOP = (26, 26, 46)       # 深蓝 #1a1a2e
BG_BOTTOM = (22, 33, 62)    # 更深的蓝 #16213e
ACCENT = (233, 69, 96)      # 强调红 #e94560
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
DARK_CARD = (15, 52, 96, 180)  # 半透明卡片

# ==================== 初始化画布 ====================
img = Image.new('RGB', (WIDTH, HEIGHT), BG_TOP)
draw = ImageDraw.Draw(img)

# 绘制渐变背景
for y in range(HEIGHT):
    ratio = y / HEIGHT
    r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * ratio)
    g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * ratio)
    b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * ratio)
    draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

# 加载字体
font_title = get_font(90)
font_sub = get_font(50)
font_price_big = get_font(120)
font_service = get_font(42)
font_price = get_font(36)
font_small = get_font(30)
font_tip = get_font(28)

# ==================== 1. 标题区域 ====================
y = 120

# 顶部装饰条
draw.rectangle([(WIDTH//2 - 80, y), (WIDTH//2 + 80, y + 8)], fill=ACCENT)
y += 40

# 主标题
title = "Python 代写服务"
bbox = draw.textbbox((0, 0), title, font=font_title)
title_w = bbox[2] - bbox[0]
draw.text(((WIDTH - title_w) // 2, y), title, font=font_title, fill=WHITE)
y += 140

# 价格大字
price_text = "30 元起"
bbox = draw.textbbox((0, 0), price_text, font=font_price_big)
price_w = bbox[2] - bbox[0]
draw.text(((WIDTH - price_w) // 2, y), price_text, font=font_price_big, fill=ACCENT)
y += 180

# 分隔线
draw.line([(100, y), (WIDTH - 100, y)], fill=(100, 100, 120), width=2)
y += 60

# ==================== 2. 服务内容 ====================
services = [
    "Python 脚本开发",
    "Excel / CSV 数据处理",
    "网页爬虫（公开数据）",
    "代码调试 & 环境配置",
    "数据可视化图表",
    "学生作业辅导答疑",
]

draw.text((100, y), "服务内容", font=font_sub, fill=WHITE)
y += 90

for service in services:
    # 圆点
    draw.ellipse([(110, y + 15), (140, y + 45)], fill=ACCENT)
    # 文字
    draw.text((170, y), service, font=font_service, fill=GRAY)
    y += 80

y += 40
draw.line([(100, y), (WIDTH - 100, y)], fill=(100, 100, 120), width=2)
y += 60

# ==================== 3. 价格表 ====================
draw.text((100, y), "价格参考", font=font_sub, fill=WHITE)
y += 100

prices = [
    ("简单脚本（50行内）", "30-50 元"),
    ("数据处理 & 清洗", "50-80 元"),
    ("带可视化的分析", "80-120 元"),
    ("爬虫（公开数据）", "60-100 元"),
    ("代码调试 / 环境配置", "30-50 元"),
]

card_margin = 80
card_w = WIDTH - card_margin * 2
row_h = 90

for item, price in prices:
    # 卡片背景
    draw.rounded_rectangle(
        [(card_margin, y), (card_margin + card_w, y + row_h)],
        radius=15,
        fill=(255, 255, 255, 30)
    )

    # 项目名称
    draw.text((card_margin + 30, y + 20), item, font=font_price, fill=WHITE)

    # 价格（右对齐）
    bbox = draw.textbbox((0, 0), price, font=font_price)
    price_w = bbox[2] - bbox[0]
    draw.text((card_margin + card_w - 30 - price_w, y + 20), price, font=font_price, fill=ACCENT)

    y += row_h + 20

y += 40

# ==================== 4. 底部信息 ====================
draw.line([(100, y), (WIDTH - 100, y)], fill=(100, 100, 120), width=2)
y += 60

# 卖点
tips = [
    "✓ 源码交付 + 详细注释",
    "✓ 远程协助跑通代码",
    "✓ 不满意免费修改 2 次",
]

for tip in tips:
    bbox = draw.textbbox((0, 0), tip, font=font_tip)
    tip_w = bbox[2] - bbox[0]
    draw.text(((WIDTH - tip_w) // 2, y), tip, font=font_tip, fill=(180, 180, 200))
    y += 60

y += 40

# 联系方式占位
contact = "📩 点击私信 / 扫码咨询"
bbox = draw.textbbox((0, 0), contact, font=font_small)
ct_w = bbox[2] - bbox[0]
draw.text(((WIDTH - ct_w) // 2, y), contact, font=font_small, fill=GRAY)

# 提示放二维码
y += 70
qr_hint = "[ 此处放你的二维码 ]"
bbox = draw.textbbox((0, 0), qr_hint, font=font_small)
qr_w = bbox[2] - bbox[0]
draw.rectangle(
    [(WIDTH//2 - 150, y), (WIDTH//2 + 150, y + 300)],
    outline=(100, 100, 120),
    width=2
)
draw.text(((WIDTH - qr_w) // 2, y + 130), qr_hint, font=font_small, fill=(100, 100, 120))

# ==================== 保存 ====================
img.save(OUTPUT_FILE)
print(f"✅ 海报已生成: {OUTPUT_FILE}")
print(f"📐 尺寸: {WIDTH}x{HEIGHT} (9:16 竖屏)")
print("💡 提示：用美图秀秀或微信打开图片，把'[此处放你的二维码]'替换成你的真实二维码")
