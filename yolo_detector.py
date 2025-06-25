# yolo_detector.py
import torch
import numpy as np
import cv2
from PIL import Image
from pathlib import Path

YOLO_MODEL_PATH = Path("custom_yolo/best.pt")
yolo_model = torch.hub.load('yolov5', 'custom', path=YOLO_MODEL_PATH, source='local', force_reload=False)

def detect_card_yolo(pil_img: Image.Image) -> Image.Image | None:
    image = np.array(pil_img.convert("RGB"))[..., ::-1]  # PIL -> np BGR
    results = yolo_model(image)
    detections = results.pandas().xyxy[0]

    if detections.empty:
        return None

    row = detections.iloc[0]
    xmin, ymin, xmax, ymax = map(int, [row['xmin'], row['ymin'], row['xmax'], row['ymax']])
    cropped = image[ymin:ymax, xmin:xmax]

    # Определим угол наклона через градиенты (Hough Transform - простой и надёжный способ)
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 200)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

    if lines is not None:
        angles = []
        for rho, theta in lines[:, 0]:
            angle_deg = np.rad2deg(theta)
            # Оставляем только почти вертикальные и горизонтальные
            if angle_deg < 10 or (80 < angle_deg < 100) or angle_deg > 170:
                if angle_deg > 90:
                    angle_deg -= 180
                angles.append(angle_deg)

        if angles:
            median_angle = np.median(angles)
            if abs(median_angle) > 2:  # Если заметен поворот
                h, w = cropped.shape[:2]
                M = cv2.getRotationMatrix2D((w / 2, h / 2), median_angle, 1)
                rotated = cv2.warpAffine(cropped, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                return Image.fromarray(cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB))

    # Если угол не найден или почти 0
    return Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
