from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

import os
import time

import cv2
import khandy
import numpy as np

from insectid import InsectDetector
from insectid import InsectIdentifier

app = FastAPI(title="Insect Detection & Identification API")

# 初始化模型
detector = InsectDetector()
identifier = InsectIdentifier()

@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    # 1. 检查文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="File must be an image.")

    # 2. 读取图像到内存
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(400, detail="Invalid image.")

    # 3. 预处理
    if max(image.shape[:2]) > 1280:
        image = khandy.resize_image_long(image, 1280)
    image_for_draw = image.copy()
    image_height, image_width = image.shape[:2]

    # 3. 预处理
    if max(image.shape[:2]) > 1280:
        image = khandy.resize_image_long(image, 1280)
    image_for_draw = image.copy()
    image_height, image_width = image.shape[:2]

    # 4. 检测 + 识别
    boxes, confs, classes = detector.detect(image)
    results_list = []

    for box, conf, class_ind in zip(boxes, confs, classes):
        box = box.astype(np.int32)
        box_width = box[2] - box[0]
        box_height = box[3] - box[1]
        if box_width < 30 or box_height < 30:
            continue

        cropped = khandy.crop_or_pad(image, box[0], box[1], box[2], box[3])
        results = identifier.identify(cropped)
        result = results[0]
        prob = result['probability']
        text = 'Unknown' if prob < 0.10 else f"{result['chinese_name']}: {prob:.3f}"

        # 绘图
        cv2.rectangle(image_for_draw, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
        position = [max(0, box[0] + 2), max(0, box[1] - 20)]
        image_for_draw = khandy.draw_text(image_for_draw, text, position, font_size=15)

        # results列表可输出化(results中存在float32)
        outputable_results = []
        for item in results:
            outputable_results.append({
                "chinese_name": str(item["chinese_name"]),
                "latin_name": str(item["latin_name"]),
                "probability": float(item["probability"])  # 转为 Python float
            })

        # 记录结果
        results_list.append({
            "bbox": box.tolist(), # 绘图框
            "results": outputable_results, # 输出
            "probability": float(prob) # 置信度
        })

    # 5. 返回：JSON
    return JSONResponse(content = {"results":results_list})


# 用于bash启动服务，本地调试
# uvicorn main:app --reload