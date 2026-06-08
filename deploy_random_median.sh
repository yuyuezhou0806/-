#!/bin/bash
# ============================================================
# 独立部署 - 随机中位数生成器
# 端口: 8088（独立端口，不动任何现有配置）
# ============================================================
set -e

SITE="random-median"
PORT="8088"
WWW="/var/www/$SITE"

echo "=== 部署 $SITE (端口 $PORT) ==="

# 1. 创建网站目录
sudo mkdir -p "$WWW"

# 2. 复制 HTML 文件（假设脚本和 HTML 在同一目录）
if [ -f "./random_median_demo.html" ]; then
    sudo cp ./random_median_demo.html "$WWW/index.html"
    echo "[OK] 文件已复制到 $WWW/index.html"
else
    echo "[ERROR] 找不到 random_median_demo.html，请先把它放到当前目录"
    exit 1
fi

# 3. 设置权限
sudo chown -R www-data:www-data "$WWW"
sudo chmod -R 755 "$WWW"

# 4. 创建独立 Nginx 配置
sudo tee "/etc/nginx/sites-available/$SITE" > /dev/null << 'NGINX'
server {
    listen PORT_PLACEHOLDER;
    server_name _;

    root /var/www/SITE_PLACEHOLDER;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # 静态文件缓存
    location ~* \.(html|css|js|png|jpg|svg|ico)$ {
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

# 替换占位符
sudo sed -i "s/PORT_PLACEHOLDER/$PORT/g" "/etc/nginx/sites-available/$SITE"
sudo sed -i "s/SITE_PLACEHOLDER/$SITE/g" "/etc/nginx/sites-available/$SITE"

# 5. 启用站点
sudo ln -sf "/etc/nginx/sites-available/$SITE" "/etc/nginx/sites-enabled/$SITE"

# 6. 开放防火墙端口（如果 ufw 开着）
if sudo ufw status | grep -q "active"; then
    sudo ufw allow "$PORT/tcp" 2>/dev/null && echo "[OK] 防火墙已开放 $PORT 端口" || true
fi

# 7. 测试并重载 Nginx
echo "--- Nginx 配置测试 ---"
sudo nginx -t && sudo systemctl reload nginx && echo "[OK] Nginx 已重载"

echo ""
echo "=============================================="
echo "  部署完成！"
echo "  访问地址: http://1.15.170.85:$PORT"
echo "=============================================="
