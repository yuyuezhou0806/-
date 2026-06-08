import re

# 特斯拉风格颜色映射
replacements = [
    # 背景色
    ('bg-zinc-900', 'bg-[#171a20]'),
    ('bg-zinc-50', 'bg-[#f4f4f4]'),
    ('bg-blue-50', 'bg-[#f4f4f4]'),
    ('bg-black/40', 'bg-black/30'),

    # 文字色
    ('text-zinc-900', 'text-[#171a20]'),
    ('text-zinc-800', 'text-[#171a20]'),
    ('text-zinc-700', 'text-[#393c41]'),
    ('text-zinc-600', 'text-[#5c5e62]'),
    ('text-zinc-500', 'text-[#5c5e62]'),
    ('text-zinc-400', 'text-[#a2a3a5]'),
    ('text-zinc-300', 'text-[#d0d1d2]'),

    # 边框色
    ('border-zinc-200', 'border-[#e2e2e2]'),
    ('border-zinc-300', 'border-[#d0d1d2]'),
    ('border-zinc-100', 'border-[#f4f4f4]'),
    ('border-blue-200', 'border-[#e2e2e2]'),
    ('border-blue-500', 'border-[#171a20]'),

    # 强调色
    ('text-blue-600', 'text-[#171a20]'),
    ('text-blue-400', 'text-[#a2a3a5]'),
    ('text-blue-900', 'text-[#171a20]'),
    ('text-blue-700', 'text-[#393c41]'),
    ('focus:ring-blue-500', 'focus:ring-[#3e6ae1]'),
    ('focus:ring-2', 'focus:ring-1'),

    # 按钮 hover
    ('hover:bg-zinc-700', 'hover:bg-[#000000]'),
    ('hover:bg-zinc-50', 'hover:bg-[#f4f4f4]'),
    ('hover:text-zinc-900', 'hover:text-[#171a20]'),
    ('hover:text-zinc-800', 'hover:text-[#171a20]'),
    ('hover:text-zinc-700', 'hover:text-[#393c41]'),
    ('hover:border-zinc-400', 'hover:border-[#171a20]'),
    ('hover:border-zinc-300', 'hover:border-[#171a20]'),

    # 圆角加大（特斯拉卡片更圆润）
    ('rounded-lg', 'rounded-2xl'),
    ('rounded-md', 'rounded-xl'),
    ('rounded-xl', 'rounded-2xl'),  # 先替换成 xl 的已经在前面被替换了

    # 阴影微调
    ('shadow-xl', 'shadow-lg'),
]

with open('page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

for old, new in replacements:
    content = content.replace(old, new)

# 修复重复替换问题：rounded-xl 被替换成 rounded-2xl，但原来的 rounded-lg 已经被替换成 rounded-2xl 了
# 所以不需要额外处理

with open('page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("特斯拉风格替换完成")
