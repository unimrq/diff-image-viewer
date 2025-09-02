from pathlib import Path
from backend.run import ImageGenerator  # 引入你整理好的模块

# 图片根目录
ROOT_DIR = Path(r"D:\AI-Photo\素材\ty").resolve()
THUMB_DIR = Path(r"D:\AI-Photo\thumbnails").resolve()

# 初始化生成器
generator = ImageGenerator(
    server_address="127.0.0.1:8180",
    input_node="203",
    output_node="794",
    noise_nodes=["736", "555"],
)