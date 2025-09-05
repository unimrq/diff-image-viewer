import os
from typing import Optional
from my_config import generator

def ensure_a_ending(filename: str) -> Optional[str]:
    """
    检查文件名是否满足规则，并返回新的文件名：
    - 已经以 a 结尾：保持不变
    - 以 b 结尾：排除（返回 None）
    - 否则：在扩展名前加上 a
    """
    valid_exts = (".jpg", ".jpeg", ".png", ".webp")
    lower_name = filename.lower()

    if not lower_name.endswith(valid_exts):
        return None  # 非图片文件，忽略

    name, ext = os.path.splitext(filename)

    if name.endswith("a"):
        return filename  # 已经以 a 结尾
    elif name.endswith("b"):
        return None      # b 结尾 → 排除
    else:
        return name + "a" + ext  # 自动加上 a


def process_folder(folder_path: str):
    """
    遍历文件夹并修正文件名
    """
    for root, _, files in os.walk(folder_path):
        for file in files:
            new_name = ensure_a_ending(file)
            if new_name is None:
                print(f"跳过: {file}")
                continue

            if new_name != file:
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, new_name)

                # 避免覆盖已有同名文件
                if os.path.exists(new_path):
                    print(f"⚠️ 已存在同名文件，跳过: {new_name}")
                    continue

                os.rename(old_path, new_path)
                print(f"重命名: {file} → {new_name}")


if __name__ == "__main__":
    folder = r"D:\AI-Photo\素材\ty\其他"  # 修改为你的文件夹路径
    process_folder(folder)
    generator.generate_batch("自动重绘NFK版v1.01.json", folder)