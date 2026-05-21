import os
import sys

# PyInstaller 打包后，资源文件在 _MEIPASS 临时目录
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_dir)

import uvicorn
from main import app

if __name__ == "__main__":
    print("=" * 50)
    print("  Guangzhou SME Digital Subsidy System")
    print("=" * 50)
    print()
    print("Starting server on http://localhost:8008")
    print("Press Ctrl+C to stop")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")
