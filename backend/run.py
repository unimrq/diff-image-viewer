import json
import os
import random
import uuid
import requests
import websocket
from loguru import logger


class ImageGenerator:
    def __init__(self, server_address, input_node, output_node, noise_nodes=None):
        self.server_address = server_address
        self.input_node = input_node
        self.noise_nodes = noise_nodes or []
        self.output_node = output_node
        self.client_id = str(uuid.uuid4())

    def _generate_seed(self):
        return random.randint(10 ** 14, 10 ** 16 - 1)

    def _queue_prompt(self, prompt):
        p = {"prompt": prompt, "client_id": self.client_id}
        res = requests.post(f"http://{self.server_address}/prompt", json=p)
        res.raise_for_status()
        return res.json()

    def _get_image(self, filename, subfolder, folder_type):
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        res = requests.get(f"http://{self.server_address}/view", params=params)
        res.raise_for_status()
        return res.content

    def _upload_image(self, filepath):
        filename = os.path.basename(filepath)
        new_filepath = os.path.join(self.upload_folder, filename)
        with open(filepath, "rb") as f:
            files = {"image": (new_filepath, f, "image/png")}
            res = requests.post(f"http://{self.server_address}/upload/image", files=files)
            res.raise_for_status()
        return new_filepath

    def _get_history(self, prompt_id):
        res = requests.get(f"http://{self.server_address}/history/{prompt_id}")
        res.raise_for_status()
        return res.json()

    def _get_images(self, prompt_id):
        ws = websocket.WebSocket()
        ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
        logger.info(f"prompt_id:{prompt_id} 监听任务中...")
        output_images = []

        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message.get("type") == "executing":
                    data = message.get("data", {})
                    if data.get("node") is None and data.get("prompt_id") == prompt_id:
                        logger.info(f"prompt_id:{prompt_id} 任务已完成")
                        break

        history = self._get_history(prompt_id)[prompt_id]

        a_image = history["outputs"]["794"]["a_images"][0]
        b_image = history["outputs"]["794"]["b_images"][0]

        for image in [a_image, b_image]:
            image_data = self._get_image(image["filename"], image["subfolder"], image["type"])
            output_images.append(image_data)

        logger.info(f"prompt_id:{prompt_id} 获取图片成功")
        return output_images

    def _parse_workflow(self, filepath, workflow):
        with open(workflow, "r", encoding="utf-8") as f:
            prompt = json.load(f)

        prompt[self.input_node]["inputs"]["image"] = filepath


        for node in self.noise_nodes:
            new_seed = self._generate_seed()
            inputs = prompt[str(node)]["inputs"]
            if "noise_seed" in inputs:
                inputs["noise_seed"] = new_seed
            elif "seed" in inputs:
                inputs["seed"] = new_seed

        prompt_id = self._queue_prompt(prompt)["prompt_id"]
        return self._get_images(prompt_id)

    def generate(self, workflow, image_path_a, image_path_b):
        """
        使用 image_path_a 作为输入，生成结果并保存到 image_path_b
        """
        # 生成图片（调用 workflow）
        images = self._parse_workflow(image_path_a, workflow)

        results = []
        if len(images) > 1:
            # 保存 b_image 到指定路径
            with open(image_path_b, "wb") as f:
                f.write(images[1])
            logger.info(f"{image_path_b} 保存完毕")
            results.append(image_path_b)
        else:
            logger.warning("生成结果中没有 b_image")

        return results
