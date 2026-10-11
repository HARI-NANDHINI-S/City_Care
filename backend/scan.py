import os
import json
import sqlite3

def scan_dir(path):
    res = []
    for root, dirs, files in os.walk(path):
        if 'node_modules' in root or '__pycache__' in root or '.git' in root or 'venv' in root:
            continue
        for f in files:
            if f.endswith(('.py', '.ts', '.tsx', '.md', '.json', '.html')):
                res.append(os.path.join(root, f))
    return res

backend_files = scan_dir(r'E:\City_Care\backend')
frontend_files = scan_dir(r'E:\City_Care\frontend')

print(f'Backend files: {len(backend_files)}')
print(f'Frontend files: {len(frontend_files)}')

db_path = r'E:\City_Care\backend\civicsense.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print('DB Tables:', [t[0] for t in tables])
    conn.close()
