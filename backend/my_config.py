import configparser
from pathlib import Path
from backend.run import ImageGenerator  # 你的模块
import sys

# 获取 exe 或脚本所在目录
if getattr(sys, "frozen", False):
    base_path = Path(sys.executable).parent  # exe 所在目录
else:
    base_path = Path(__file__).parent       # 脚本所在目录

config_path = base_path / "config.ini"

if not config_path.exists():
    raise FileNotFoundError(f"配置文件未找到: {config_path}")

# 读取配置
config = configparser.ConfigParser()
config.read(config_path, encoding="utf-8")

# 路径
ROOT_DIR = Path(config["paths"]["root_dir"]).resolve()
THUMB_DIR = Path(config["paths"]["thumb_dir"]).resolve()

# 密码
PASSWORD = config["auth"]["password"]

# 生成器参数
server_address = config["generator"]["server_address"]
input_node = config["generator"]["input_node"]
output_node = config["generator"]["output_node"]
noise_nodes = [n.strip() for n in config["generator"]["noise_nodes"].split(",")]

# 初始化生成器
generator = ImageGenerator(
    server_address=server_address,
    input_node=input_node,
    output_node=output_node,
    noise_nodes=noise_nodes
)
