# 差分图片浏览器 (Diff Image Viewer)

差分图片浏览器是一款轻量、易用的图片对比工具，可以快速浏览指定文件夹中的图片，并通过“擦除式”效果，将两张图片重叠显示，直观查看差异。非常适合图片比对、差异分析或版本校验场景。

---

## 功能预览

### 1. 文件浏览功能
可以方便地浏览指定目录下的图片文件。  

![img.png](res/img.png)

### 2. 图片差分功能
通过“擦除”操作查看两张图片的差异，支持调整橡皮擦大小，实时显示差异区域。  

![img_1.png](res/img_1.png)

---

## 使用方法

### 1. 配置图片目录
在 `backend/main.py` 中修改 `ROOT_DIR` 为你想浏览的图片文件夹：  

```
ROOT_DIR = Path(r"D:\AI-Photo\素材\diff").resolve()
```

### 2. 安装前端依赖
切换到 frontend 文件夹并执行：
```
npm install
```

### 3. 安装 Python 依赖
在 Python 环境中执行：
```
pip install -r requirements.txt
```

### 4. 启动程序
在 Python 环境中执行：
```
python start_all.py
```

## 特别注意
本应用的图片识别方式较为简单，系统仅能识别成对的差分图片，文件名需分别为 XXX+a.jpg 和 XXX+b.jpg。如有特殊需求，可根据实际情况自行修改代码实现。