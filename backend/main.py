import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from loguru import logger
from PIL import Image
from starlette.staticfiles import StaticFiles
# -----------------------
# 本地模块导入
# -----------------------
from backend.resize import generate_thumbnail, process_folder
from my_config import ROOT_DIR, THUMB_DIR, generator, PASSWORD


# -----------------------
# FastAPI 初始化
# -----------------------
app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_host = request.client.host  # 获取客户端 IP
    method = request.method
    path = request.url.path
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"[{now}] {client_host} {method} {path}")

    response = await call_next(request)
    return response

# 缓存目录
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# 任务状态缓存
TASK_STATUS = {}



TOKEN_FILE = Path("valid_tokens.json")

# 初始化 token 集合
if TOKEN_FILE.exists():
    with open(TOKEN_FILE, "r") as f:
        VALID_TOKENS = set(json.load(f))
else:
    VALID_TOKENS = set()

def save_tokens():
    with open(TOKEN_FILE, "w") as f:
        json.dump(list(VALID_TOKENS), f)


# -----------------------
# CORS 设置
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# -----------------------
# dist 路径（打包后/开发模式）
# -----------------------
if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

dist_path = Path(base_path) / "dist"

# 静态文件挂载
if (dist_path / "assets").exists():
    app.mount("/assets", StaticFiles(directory=dist_path / "assets"), name="assets")

# -----------------------
# 模型定义
# -----------------------
class RegenRequest(BaseModel):
    aPath: str   # 输入图路径
    bPath: str   # 输出图路径


class LoginRequest(BaseModel):
    password: str


# -----------------------
# API：鉴权
# -----------------------
security = HTTPBearer()


@app.post("/api/login")
async def login(req: LoginRequest):
    if req.password == PASSWORD:
        now = str(time.time())
        token = str(uuid.uuid5(uuid.NAMESPACE_DNS, now))
        VALID_TOKENS.add(token)
        save_tokens()
        return {"success": True, "token": token}
    raise HTTPException(status_code=401, detail="密码错误")


def check_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="未授权")
    return token


# -----------------------
# API：目录操作
# -----------------------
@app.get("/api/list")
def list_dir(dir: str = "", token: str = Depends(check_auth)):
    folder = ROOT_DIR / dir
    if not folder.exists() or not folder.is_dir():
        return JSONResponse([], status_code=404)

    result = [
        {
            "name": item.name,
            "type": "folder" if item.is_dir() else "file",
            "path": str(Path(dir) / item.name).replace("\\", "/"),
        }
        for item in folder.iterdir()
    ]
    return result


# -----------------------
# API：图片/缩略图
# -----------------------
@app.get("/images/{path:path}")
def serve_image(path: str):
    file_path = ROOT_DIR / path
    if not file_path.exists() or not file_path.is_file():
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(file_path, headers={"Access-Control-Allow-Origin": "*"})



@app.get("/thumbnails/{path:path}")
def serve_thumbnail(path: str):
    file_path = THUMB_DIR / path
    if not file_path.exists() or not file_path.is_file():
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(file_path, headers={"Access-Control-Allow-Origin": "*"})


# -----------------------
# API：图像生成
# -----------------------
def regenerate_task(task_id: str, file_path_a: Path, file_path_b: Path):
    try:
        TASK_STATUS[task_id] = "running"
        logger.info(f"[{task_id}] 开始生成 A={file_path_a}, B={file_path_b}")
        generator.generate("自动重绘NFK版v1.01.json", str(file_path_a), str(file_path_b))
        TASK_STATUS[task_id] = "done"
        logger.info(f"[{task_id}] 生成完成")
    except Exception as e:
        TASK_STATUS[task_id] = f"error: {e}"
        logger.error(f"[{task_id}] 生成失败: {e}")


@app.post("/api/regenerate")
async def regenerate(req: RegenRequest, background_tasks: BackgroundTasks):
    # ---------- 路径解析 ----------
    def parse_path(url: str) -> Path:
        parsed = urlparse(url)
        rel = unquote(parsed.path)
        if "/images/" in rel:
            rel = rel.split("/images/", 1)[1]
        return ROOT_DIR / rel

    file_path_a = parse_path(req.aPath)
    file_path_b = parse_path(req.bPath)

    if not file_path_a.exists():
        raise HTTPException(status_code=400, detail=f"A 图文件不存在: {file_path_a}")

    file_path_b.parent.mkdir(parents=True, exist_ok=True)

    # ---------- 生成任务 ----------
    task_id = str(uuid.uuid4())
    TASK_STATUS[task_id] = "pending"
    background_tasks.add_task(regenerate_task, task_id, file_path_a, file_path_b)

    # ---------- 缩略图 ----------
    thumb_a = THUMB_DIR / file_path_a.relative_to(ROOT_DIR)
    thumb_b = THUMB_DIR / file_path_b.relative_to(ROOT_DIR)
    thumb_a.parent.mkdir(parents=True, exist_ok=True)
    thumb_b.parent.mkdir(parents=True, exist_ok=True)
    generate_thumbnail(file_path_a, thumb_a)
    generate_thumbnail(file_path_b, thumb_b)

    return {"status": "accepted", "task_id": task_id}


@app.get("/api/task_status/{task_id}")
async def task_status(task_id: str):
    return {"task_id": task_id, "status": TASK_STATUS.get(task_id, "not found")}


@app.post("/api/resize")
async def trigger_resize(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_folder)
    return {"status": "accepted"}


@app.post("/api/compress")
async def compress_images(req: RegenRequest):
    """压缩图片并返回缓存路径"""
    def parse_path(url: str) -> Path:
        parsed = urlparse(url)
        return ROOT_DIR / unquote(parsed.path).split("/images/")[-1]

    file_path_a = parse_path(req.aPath)
    file_path_b = parse_path(req.bPath)

    if not file_path_a.exists() or not file_path_b.exists():
        raise HTTPException(status_code=400, detail="原图不存在")

    # ---------- 压缩 ----------
    def compress_image(src: Path, dst: Path, max_size=(800, 800), quality=50):
        with Image.open(src) as im:
            im.thumbnail(max_size)
            im.save(dst, quality=quality)

    a_compress = CACHE_DIR / file_path_a.name
    b_compress = CACHE_DIR / file_path_b.name
    compress_image(file_path_a, a_compress)
    compress_image(file_path_b, b_compress)

    return {
        "aCompressed": f"/api/cache/{a_compress.name}",
        "bCompressed": f"/api/cache/{b_compress.name}",
    }


@app.get("/api/cache/{filename}")
def serve_cache_image(filename: str):
    file_path = CACHE_DIR / filename
    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(file_path, headers={"Access-Control-Allow-Origin": "*"})




# -----------------------
# Vue 路由处理
# -----------------------
@app.get("/{full_path:path}")
def serve_vue(full_path: str):
    if full_path.startswith("api"):
        return {"detail": "Not Found"}

    index_file = dist_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    return {"detail": "index.html not found"}


@app.get("/favicon.ico")
def favicon():
    return FileResponse(dist_path / "favicon.ico")