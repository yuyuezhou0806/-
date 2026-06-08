#!/bin/bash
# ============================================================
# 独立部署 - 随机中位数生成器 (含后端统计)
# 端口: 8088 | 后端: 127.0.0.1:8001
# 不动任何现有配置
# ============================================================
set -e

SITE="random-median"
PORT="8088"
WWW="/var/www/$SITE"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Deploy $SITE (port $PORT) ==="

# 1. Install deps
echo ">>> Installing Python deps..."
pip3 install fastapi uvicorn --break-system-packages -q 2>/dev/null || sudo pip3 install fastapi uvicorn --break-system-packages -q

# 2. Setup directory
echo ">>> Setting up $WWW..."
sudo mkdir -p "$WWW"
sudo cp "$SCRIPT_DIR/random_median_demo.html" "$WWW/index.html"
sudo cp "$SCRIPT_DIR/random_median_server.py" "$WWW/server.py"
sudo chown -R www-data:www-data "$WWW"
sudo chmod -R 755 "$WWW"

# 3. systemd service
echo ">>> Creating systemd service..."
sudo tee "/etc/systemd/system/$SITE.service" > /dev/null << UNIT
[Unit]
Description=Random Median Generator Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/$SITE
ExecStart=/usr/bin/python3 /var/www/$SITE/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable "$SITE.service"
sudo systemctl restart "$SITE.service"
echo ">>> Backend started"

# 4. Nginx config
echo ">>> Configuring nginx..."
sudo tee "/etc/nginx/sites-available/$SITE" > /dev/null << NGINX
server {
    listen $PORT;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
NGINX

sudo ln -sf "/etc/nginx/sites-available/$SITE" "/etc/nginx/sites-enabled/$SITE"

# 5. Firewall
if sudo ufw status 2>/dev/null | grep -q "active"; then
    sudo ufw allow "$PORT/tcp" 2>/dev/null || true
fi

# 6. Reload nginx
sudo nginx -t && sudo systemctl reload nginx

# 7. Verify
sleep 1
HTTP=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/" 2>/dev/null || echo "000")
echo ""
echo "=============================================="
echo "  Local check: HTTP $HTTP"
echo "  Public URL:  http://1.15.170.85:$PORT"
echo "=============================================="
