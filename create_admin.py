import sqlite3, hashlib, datetime

db = '/var/www/idi-defects/users.db'
pw = hashlib.sha256('123456'.encode()).hexdigest()
conn = sqlite3.connect(db)

# Find max id
max_id = conn.execute('SELECT MAX(id) FROM users').fetchone()[0] or 0
new_id = max_id + 1

conn.execute(
    'INSERT INTO users (id, username, password_hash, is_admin, created_at) VALUES (?, ?, ?, 1, datetime("now"))',
    [new_id, 'yyz', pw]
)
conn.commit()

rows = conn.execute('SELECT id, username, is_admin FROM users ORDER BY id').fetchall()
print('Users:')
for r in rows:
    tag = '管理员' if r[2] else '普通'
    print(f'  {r[0]}. {r[1]} - {tag}')
conn.close()
