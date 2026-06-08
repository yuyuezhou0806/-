with open('/var/www/idi-defects/auth_server.py', 'r') as f:
    content = f.read()

old = '@app.get("/api/stats")'
new = '@app.get("/api/admin/stats")\ndef admin_stats_endpoint(admin: str = Depends(require_admin)):\n    return get_stats()\n\n@app.get("/api/stats")'

content = content.replace(old, new)

with open('/var/www/idi-defects/auth_server.py', 'w') as f:
    f.write(content)

print('Fixed')
