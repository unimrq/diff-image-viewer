import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from loguru import logger

from backend.resize import generate_thumbnail, process_folder
from my_config import ROOT_DIR, THUMB_DIR, generator
from urllib.parse import urlparse, unquote


app = FastAPI()

# -----------------------
# CORS 设置（允许前端访问所有接口）
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# API：列出目录内容
# -----------------------
@app.get("/api/list")
def list_dir(dir: str = ""):
    folder = ROOT_DIR / dir
    if not folder.exists() or not folder.is_dir():
        return JSONResponse([], status_code=404)

    result = []
    for item in folder.iterdir():
        result.append({
            "name": item.name,
            "type": "folder" if item.is_dir() else "file",
            "path": str(Path(dir) / item.name).replace("\\", "/")
        })
    return result

# -----------------------
# API：返回图片文件，并加 CORS
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
# 生成图片相关
# -----------------------
class RegenRequest(BaseModel):
    aPath: str   # 输入图路径
    bPath: str   # 输出图路径

# 任务状态缓存
TASK_STATUS = {}

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

@app.post("/regenerate")
async def regenerate(req: RegenRequest, background_tasks: BackgroundTasks):
    # 解析 aPath
    parsed_a = urlparse(req.aPath)
    rel_a = unquote(parsed_a.path)  # 解码 URL 中的 %20 等
    if "/images/" in rel_a:
        rel_a = rel_a.split("/images/", 1)[1]
    file_path_a = ROOT_DIR / rel_a

    # 解析 bPath
    parsed_b = urlparse(req.bPath)
    rel_b = unquote(parsed_b.path)
    if "/images/" in rel_b:
        rel_b = rel_b.split("/images/", 1)[1]
    file_path_b = ROOT_DIR / rel_b

    if not file_path_a.exists():
        raise HTTPException(status_code=400, detail=f"A 图文件不存在: {file_path_a}")

    # 确保输出目录存在
    file_path_b.parent.mkdir(parents=True, exist_ok=True)

    # 生成唯一任务ID
    task_id = str(uuid.uuid4())
    TASK_STATUS[task_id] = "pending"

    # 启动后台任务
    background_tasks.add_task(regenerate_task, task_id, file_path_a, file_path_b)

    # 生成缩略图路径
    thumb_a = THUMB_DIR / file_path_a.relative_to(ROOT_DIR)
    thumb_b = THUMB_DIR / file_path_b.relative_to(ROOT_DIR)

    # 确保目录存在
    thumb_a.parent.mkdir(parents=True, exist_ok=True)
    thumb_b.parent.mkdir(parents=True, exist_ok=True)

    # 生成缩略图
    generate_thumbnail(file_path_a, thumb_a)
    generate_thumbnail(file_path_b, thumb_b)

    return {"status": "accepted", "task_id": task_id}

@app.get("/task_status/{task_id}")
async def task_status(task_id: str):
    return {"task_id": task_id, "status": TASK_STATUS.get(task_id, "not found")}

@app.post("/resize")
async def trigger_resize(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_folder)
    return {"status": "accepted"}