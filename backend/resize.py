from pathlib import Path
from PIL import Image
from my_config import ROOT_DIR, THUMB_DIR

THUMB_DIR.mkdir(exist_ok=True)

# 缩略图大小
THUMB_SIZE = (500, 500)

def generate_thumbnail(src_path: Path, dst_path: Path):
    try:
        with Image.open(src_path) as img:
            img.thumbnail(THUMB_SIZE)  # 保持比例缩小
            img.save(dst_path)
            print(f"缩略图生成: {dst_path.name}")
    except Exception as e:
        print(f"生成缩略图失败 {src_path.name}: {e}")

def process_folder():
    for img_file in ROOT_DIR.rglob("*.*"):  # 遍历所有子目录和文件
        if img_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
            # 缩略图路径和原图相同文件名
            relative_path = img_file.relative_to(ROOT_DIR)
            thumb_path = THUMB_DIR / relative_path
            thumb_path.parent.mkdir(parents=True, exist_ok=True)  # 创建子目录
            if not thumb_path.exists():  # 避免重复生成
                generate_thumbnail(img_file, thumb_path)

if __name__ == "__main__":
    process_folder()
    print("所有缩略图生成完成")