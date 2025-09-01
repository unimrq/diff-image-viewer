from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

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

# 图片根目录
ROOT_DIR = Path(r"D:\AI-Photo\素材\ytm").resolve()
THUMB_DIR = Path(r"D:\AI-Photo\thumbnails").resolve()
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

    # 在 FileResponse 里加 headers，保证跨域
    return FileResponse(file_path, headers={"Access-Control-Allow-Origin": "*"})


@app.get("/thumbnails/{path:path}")
def serve_thumbnail(path: str):
    file_path = THUMB_DIR / path
    if not file_path.exists() or not file_path.is_file():
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(file_path, headers={"Access-Control-Allow-Origin": "*"})