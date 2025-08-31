import subprocess
import os
import signal
import sys

# 项目目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")  # Vue 前端目录
BACKEND_DIR = os.path.join(BASE_DIR, "backend")    # Python 后端目录

# 启动前端
frontend_proc = subprocess.Popen(
    ["npm", "run", "dev"],
    cwd=FRONTEND_DIR,
    shell=True
)

# 启动后端
backend_proc = subprocess.Popen(
    ["python", "-m", "uvicorn", "main:app", "--reload"],
    cwd=BACKEND_DIR,
    shell=True
)

def shutdown(signal_num, frame):
    print("\nStopping processes...")
    for proc in [frontend_proc, backend_proc]:
        if proc.poll() is None:  # 进程还在运行
            proc.send_signal(signal.SIGINT)
    sys.exit(0)

# 捕获 Ctrl+C
signal.signal(signal.SIGINT, shutdown)

# 等待两个进程结束
frontend_proc.wait()
backend_proc.wait()
